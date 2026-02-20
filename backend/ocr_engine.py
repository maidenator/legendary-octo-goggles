"""
Ayahay SmartScan - OCR Engine (The Brain)
Processes scanned PDFs and images to extract and validate shipping container IDs.

Supports:
  - PDF input (via pymupdf — no Poppler binary required)
  - JPEG/PNG image input
  - Adaptive thresholding for documents with shadows/uneven lighting
  - Container ID format: ABCD1234567 or MSCU 123456-7
"""

import re
import platform
import warnings
from pathlib import Path
from typing import Optional, Dict, List

try:
    import cv2
    import numpy as np
    import warnings
    warnings.filterwarnings("ignore") # Suppress MINGW Numpy warnings on Windows
except Exception as e:
    warnings.warn(f"OpenCV unavailable: {e}. Install opencv-python-headless.")
    cv2 = None
    np = None

try:
    import pytesseract
except Exception as e:
    warnings.warn(f"pytesseract unavailable: {e}. Install pytesseract.")
    pytesseract = None

try:
    import fitz  # pymupdf
except Exception as e:
    warnings.warn(f"pymupdf unavailable: {e}. Install pymupdf for PDF support.")
    fitz = None

from stdnum import iso6346

# ---------------------------------------------------------------------------
# Windows Tesseract binary path
# ---------------------------------------------------------------------------
if platform.system() == "Windows" and pytesseract is not None:
    for _path in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]:
        if Path(_path).exists():
            pytesseract.pytesseract.tesseract_cmd = _path
            break


# ---------------------------------------------------------------------------
# Container ID regex
# Matches:  MSCU1234567  |  MSCU 123456-7  |  MSCU123456-7  |  MSCU 1234567
# ---------------------------------------------------------------------------
_CONTAINER_ID_PATTERN = re.compile(r"[A-Z]{4}\s?\d{6}-?\d")


def _normalize_id(raw: str) -> str:
    """
    Clean up and repair common OCR misreadings in container IDs.
    Shipping container IDs (ISO 6346) are 4 letters + 7 digits.
    """
    # Remove all non-alphanumeric noise
    clean = re.sub(r"[^A-Za-z0-9]", "", raw).upper()
    
    if len(clean) != 11:
        return clean

    # Split into Alpha(4) and Numeric(7)
    prefix = clean[:4]
    suffix = clean[4:]

    # Repair prefix: numbers to letters (common OCR errors)
    # 0 -> O, 1 -> I, 5 -> S, 8 -> B, 2 -> Z
    repair_map_alpha = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z"}
    prefix = "".join(repair_map_alpha.get(c, c) for c in prefix)

    # Repair suffix: letters to numbers
    # O -> 0, I -> 1, S -> 5, B -> 8, Z -> 2, G -> 6 (or 9)
    repair_map_num = {"O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "G": "6"}
    suffix = "".join(repair_map_num.get(c, c) for c in suffix)

    return prefix + suffix


# ---------------------------------------------------------------------------
# ContainerOCREngine class
# ---------------------------------------------------------------------------

class ContainerOCREngine:
    """
    End-to-end pipeline: file → preprocessed image → OCR text → container ID.

    Usage:
        engine = ContainerOCREngine()
        result = engine.process(Path("manifest.pdf"))
    """

    # Tesseract config: full OEM neural net, assume single column of text of variable sizes
    # PSM 4 + DPI 300 is optimal for the manifest grid resolution sent by the frontend
    _TESS_CONFIG = r"--oem 3 --psm 4 --dpi 300"

    def load_file(self, file_path: Path) -> "np.ndarray":
        """
        Load a PDF (first page) or an image file into a CV2 BGR array.

        Raises:
            ImportError: if the required library isn't installed.
            ValueError:  if the file can't be read.
        """
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            if fitz is None:
                raise ImportError("pymupdf is required for PDF files. Run: pip install pymupdf")
            doc = fitz.open(str(file_path))
            page = doc.load_page(0)
            # Render at 2× DPI (150 dpi default → 300 dpi) for sharper OCR
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            doc.close()
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, 3
            )
            # pymupdf returns RGB; OpenCV expects BGR
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        else:
            if cv2 is None:
                raise ImportError("OpenCV is required. Run: pip install opencv-python-headless")
            img = cv2.imread(str(file_path))
            if img is None:
                raise ValueError(f"Could not read image from {file_path}")
            return img

    def preprocess(self, img: "np.ndarray") -> "np.ndarray":
        """
        Convert to grayscale and apply adaptive thresholding.

        Adaptive (Gaussian) thresholding handles uneven lighting and shadows
        on physical documents much better than a single global Otsu threshold.
        """
        if cv2 is None:
            raise ImportError("OpenCV is required for preprocessing.")

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Strong edge-preserving denoise (better for OCR than NlMeans)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # 3. Adaptive Gaussian threshold → pure black-on-white
        # blockSize 31 is roughly 1-2x the size of characters in high-res images
        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=31,   
            C=12,           
        )

        # Save preprocessed image for debugging
        cv2.imwrite("debug_thresh.png", thresh)

        return thresh

    def extract_text(self, preprocessed_img: "np.ndarray") -> str:
        """Run Tesseract OCR on a preprocessed CV2 image and return raw text."""
        if pytesseract is None:
            raise ImportError("pytesseract is required. Run: pip install pytesseract")
        return pytesseract.image_to_string(preprocessed_img, config=self._TESS_CONFIG)

    def find_container_ids(self, text: str) -> List[str]:
        """
        Extract and normalize potential container IDs with fuzzy logic.
        Matches 11-character alphanumeric sequences and applies repairs.
        """
        # NO \b word boundaries: IDs are often stuck to table lines like |_MSCU...|
        # We look for any cluster of 10-12 alphanumeric chars that could be an ID.
        fuzzy_pattern = re.compile(r"[A-Z0-9]{4,5}\s?[A-Z0-9]{5,7}", re.IGNORECASE)
        raw_matches = fuzzy_pattern.findall(text)
        
        seen: set = set()
        result: List[str] = []
        for raw in raw_matches:
            normalized = _normalize_id(raw)
            if len(normalized) == 11 and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

    def validate(self, container_id: str) -> Dict:
        """
        Validate a compact 11-char container ID against ISO 6346 check-digit rules.

        Returns:
            dict with keys: valid (bool), container_id, check_digit, error.
        """
        result = {
            "valid": False,
            "container_id": container_id,
            "check_digit": None,
            "error": None,
        }
        if len(container_id) != 11:
            result["error"] = f"Expected 11 chars, got {len(container_id)}"
            return result
        try:
            iso6346.validate(container_id)
            result["valid"] = True
            result["check_digit"] = container_id[-1]
        except Exception as exc:
            result["error"] = str(exc)
        return result

    def process(self, file_path: Path) -> Dict:
        """
        Full pipeline: load → preprocess → OCR → find IDs → validate.

        Returns:
            {
                'success': bool,
                'raw_text': str,
                'container_ids_found': List[str],
                'validated_ids': List[dict],
                'best_match': dict | None,
                'error': str | None,
            }
        """
        output = {
            "success": False,
            "raw_text": "",
            "container_ids_found": [],
            "validated_ids": [],
            "best_match": None,
            "error": None,
        }
        try:
            img = self.load_file(file_path)
            preprocessed = self.preprocess(img)
            raw_text = self.extract_text(preprocessed)
            output["raw_text"] = raw_text

            ids = self.find_container_ids(raw_text)
            output["container_ids_found"] = ids

            if not ids:
                output["error"] = "No container IDs found in document"
                return output

            validated = [self.validate(cid) for cid in ids]
            output["validated_ids"] = validated
            output["success"] = True

            for v in validated:
                if v["valid"]:
                    output["best_match"] = v
                    break

            if output["best_match"] is None:
                output["error"] = "IDs found but none passed ISO 6346 check-digit validation"
                output["success"] = False

        except Exception as exc:
            import traceback
            traceback.print_exc()
            output["error"] = str(exc)

        return output


# ---------------------------------------------------------------------------
# Module-level helper — keeps main.py and database.py unchanged
# ---------------------------------------------------------------------------
_engine = ContainerOCREngine()


def process_image(image_path: Path) -> Dict:
    """
    Drop-in replacement for the old module-level process_image().
    Accepts both PDF and image files.
    """
    return _engine.process(image_path)

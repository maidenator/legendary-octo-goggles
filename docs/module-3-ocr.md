## Module 3 – OCR Engine (The Brain)

**Purpose:** Extract container IDs from scanned manifest images using OCR, then validate them using ISO 6346 check-digit algorithm.

### Tech & Files

- **Stack:** OpenCV (image preprocessing), PyTesseract (OCR), python-stdnum (ISO 6346 validation), regex.
- **Files:**
  - `backend/ocr_engine.py` – OCR processing module.
  - Updated `backend/main.py` – integrates OCR into `/scan` endpoint.
  - Updated `backend/requirements.txt` – adds `opencv-python`, `pytesseract`, `python-stdnum`.

### Image Preprocessing (`preprocess_image`)

- Reads image with `cv2.imread()`.
- Converts to grayscale (`cv2.COLOR_BGR2GRAY`).
- Applies binary thresholding (`cv2.THRESH_BINARY + cv2.THRESH_OTSU`) for automatic threshold calculation.
- Returns preprocessed image matrix.

### OCR Text Extraction (`extract_text`)

- Takes image path, preprocesses it.
- Runs PyTesseract with custom config:
  - `--oem 3` (LSTM OCR engine).
  - `--psm 6` (assume uniform block of text).
  - `tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (alphanumeric only).
- Returns extracted text string.

### Container ID Extraction (`find_container_ids`)

- Uses regex pattern: `[A-Z]{4}\d{7}` (4 uppercase letters + 7 digits).
- Finds all matches in text.
- Removes duplicates while preserving order.
- Returns list of found container ID strings.

### ISO 6346 Validation (`validate_container_id`)

- Validates container ID format (11 characters total).
- Structure:
  - Owner code: positions 0-2 (3 letters).
  - Equipment code: position 3 (1 letter).
  - Serial number: positions 4-9 (6 digits).
  - Check digit: position 10 (1 digit).
- Uses `python-stdnum.iso6346.validate()` to verify check digit.
- Returns validation result dictionary:
  ```python
  {
      'valid': bool,
      'container_id': str,
      'check_digit': str or None,
      'error': str or None
  }
  ```

### Main Processing Function (`process_image`)

- Orchestrates the full pipeline:
  1. Extract text via OCR.
  2. Find container IDs using regex.
  3. Validate each found ID.
  4. Return first valid ID as "best_match".
- Returns comprehensive result dictionary:
  ```python
  {
      'success': bool,
      'raw_text': str,
      'container_ids_found': List[str],
      'validated_ids': List[Dict],
      'best_match': Dict or None,
      'error': str or None
  }
  ```

### Integration with FastAPI (`/scan` endpoint)

- After saving uploaded image, calls `process_image(file_path)`.
- Extracts `container_id` and `validation_status` from OCR result.
- Returns enhanced JSON response with OCR results:
  - `container_id`: First valid container ID found (or `null`).
  - `validation_status`: "valid" or `null`.
  - `container_ids_found`: All container IDs found in image.
  - `raw_text_preview`: First 200 chars of OCR text (for debugging).
  - `error`: Error message if OCR failed.

### Dependencies

- **opencv-python**: Image preprocessing (grayscale, thresholding).
- **pytesseract**: OCR engine wrapper (requires Tesseract binary installed separately).
- **python-stdnum**: ISO 6346 container ID validation.

### Installation Notes

**Important:** PyTesseract requires the Tesseract OCR binary to be installed on the system:

- **Windows:** Download installer from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki) or use `choco install tesseract`.
- **Linux:** `sudo apt-get install tesseract-ocr` (Debian/Ubuntu) or `sudo yum install tesseract` (RHEL/CentOS).
- **macOS:** `brew install tesseract`.

The Python package (`pytesseract`) is just a wrapper; the binary must be installed separately.

### Error Handling

- Handles image read failures, OCR errors, and validation failures gracefully.
- Returns detailed error messages in result dictionary.
- FastAPI endpoint continues to return 200 OK even if OCR fails (with error details in response).

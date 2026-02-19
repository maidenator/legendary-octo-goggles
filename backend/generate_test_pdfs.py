"""
generate_test_pdfs.py — Ayahay SmartScan Test File Generator

Stamps container IDs onto docs/template.pdf to create realistic test PDFs
for OCR validation.

Usage:
    py generate_test_pdfs.py                        # default batch (3 valid + 2 invalid)
    py generate_test_pdfs.py --id MSCU1234568       # single custom ID
    py generate_test_pdfs.py --count 10             # 10 valid test PDFs
    py generate_test_pdfs.py --output ./my_tests    # custom output folder
    py generate_test_pdfs.py --list                 # list available prefixes
"""

import argparse
import random
import string
import sys
from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    print("ERROR: pymupdf is required. Run: pip install pymupdf")
    sys.exit(1)

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

# ---------------------------------------------------------------------------
# Image Augmentation Functions
# ---------------------------------------------------------------------------

def add_blur(img: np.ndarray) -> np.ndarray:
    if random.random() > 0.5:
        k = random.choice([3, 5])
        return cv2.GaussianBlur(img, (k, k), 0)
    else:
        k = random.choice([5, 7, 9])
        kernel = np.zeros((k, k))
        if random.random() > 0.5:
            kernel[:, int((k-1)/2)] = np.ones(k)
        else:
            kernel[int((k-1)/2), :] = np.ones(k)
        kernel /= k
        return cv2.filter2D(img, -1, kernel)

def add_crumple(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    shadow_map = np.ones((h, w), dtype=np.float32)
    for _ in range(random.randint(2, 5)):
        x1, y1 = random.randint(0, w), random.randint(0, h)
        x2, y2 = random.randint(0, w), random.randint(0, h)
        cv2.line(shadow_map, (x1, y1), (x2, y2), 0.85, thickness=random.randint(10, 40))
        cv2.line(shadow_map, (x1, y1), (x2, y2), 0.95, thickness=random.randint(40, 80))
    shadow_map = cv2.GaussianBlur(shadow_map, (51, 51), 0)
    
    out = img.astype(np.float32)
    if out.ndim == 3 and out.shape[2] >= 3:
        for i in range(3):
            out[:,:,i] = out[:,:,i] * shadow_map
    return np.clip(out, 0, 255).astype(np.uint8)

def add_spill(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    overlay = img.copy()
    for _ in range(random.randint(1, 4)):
        center = (random.randint(0, w), random.randint(0, h))
        radius = random.randint(30, 200)
        points = []
        for angle in np.linspace(0, 2 * np.pi, 10, endpoint=False):
            r = radius + random.randint(-radius//3, radius//3)
            pts_x = int(center[0] + r * np.cos(angle))
            pts_y = int(center[1] + r * np.sin(angle))
            points.append([pts_x, pts_y])
        pts = np.array(points, np.int32).reshape((-1, 1, 2))
        color = (130, 180, 210) # BGR yellowish/brownish liquid
        cv2.fillPoly(overlay, [pts], color)
        
    alpha = random.uniform(0.1, 0.4)
    return cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

def add_bad_lighting(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.float32)
    center = (random.randint(0, w), random.randint(0, h))
    cv2.circle(mask, center, random.randint(300, 800), 1.2, -1)
    mask = cv2.GaussianBlur(mask, (101, 101), 0) + 0.4
    mask = np.clip(mask, 0, 1)
    
    out = img.astype(np.float32)
    if out.ndim == 3 and out.shape[2] >= 3:
        for i in range(3):
            out[:,:,i] = out[:,:,i] * mask
    return np.clip(out, 0, 255).astype(np.uint8)

def add_tears(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    for _ in range(random.randint(1, 3)):
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        points = []
        if edge == 'left':
            y_start, y_end = sorted([random.randint(0, h), random.randint(0, h)])
            points.append([0, y_start])
            for y in range(y_start, y_end, max(1, (y_end-y_start)//5)):
                points.append([random.randint(10, 80), y])
            points.append([0, y_end])
        elif edge == 'right':
            y_start, y_end = sorted([random.randint(0, h), random.randint(0, h)])
            points.append([w, y_start])
            for y in range(y_start, y_end, max(1, (y_end-y_start)//5)):
                points.append([w - random.randint(10, 80), y])
            points.append([w, y_end])
        elif edge == 'top':
            x_start, x_end = sorted([random.randint(0, w), random.randint(0, w)])
            points.append([x_start, 0])
            for x in range(x_start, x_end, max(1, (x_end-x_start)//5)):
                points.append([x, random.randint(10, 80)])
            points.append([x_end, 0])
        else:
            x_start, x_end = sorted([random.randint(0, w), random.randint(0, w)])
            points.append([x_start, h])
            for x in range(x_start, x_end, max(1, (x_end-x_start)//5)):
                points.append([x, h - random.randint(10, 80)])
            points.append([x_end, h])
            
        pts = np.array(points, np.int32)
        cv2.fillPoly(img, [pts], (255, 255, 255))
    return img

def augment_image(img: np.ndarray) -> np.ndarray:
    if cv2 is None or np is None:
        print("WARNING: OpenCV/NumPy not installed. Cannot apply augmentations.")
        return img
    funcs = [add_blur, add_crumple, add_spill, add_bad_lighting, add_tears]
    random.shuffle(funcs)
    for f in funcs[:random.randint(1, 3)]:
        img = f(img)
    return img

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR   = Path(__file__).parent
TEMPLATE_PDF = SCRIPT_DIR.parent / "docs" / "template.pdf"
import time
DEFAULT_OUT  = SCRIPT_DIR / "test_pdfs" / str(int(time.time()))

# Common shipping line prefixes (owner codes must end in U per ISO 6346)
PREFIXES = [
    "MSCU",  # MSC
    "TCKU",  # Triton
    "HLXU",  # Hapag-Lloyd
    "MSKU",  # Maersk
    "CMAU",  # CMA CGM
    "APHU",  # APL
    "EVRU",  # Evergreen
    "YMLU",  # Yang Ming
    "OOLU",  # OOCL
    "CSNU",  # COSCO
]

# ---------------------------------------------------------------------------
# ISO 6346 check-digit computation
# ---------------------------------------------------------------------------
from stdnum import iso6346

def compute_check_digit(owner_code: str, category: str, serial: str) -> int:
    """
    Compute the ISO 6346 check digit using stdnum.
    """
    return int(iso6346.calc_check_digit(owner_code + category + serial))


def make_valid_container_id(prefix: str = None) -> str:
    """Generate a random container ID that passes ISO 6346 check-digit validation."""
    if prefix is None:
        prefix = random.choice(PREFIXES)
    serial = "".join(random.choices(string.digits, k=6))
    check  = compute_check_digit(prefix[:3], prefix[3], serial)
    return f"{prefix}{serial}{check}"


def make_invalid_checkdigit_id(prefix: str = None) -> str:
    """Generate a container ID with an intentionally wrong check digit."""
    if prefix is None:
        prefix = random.choice(PREFIXES)
    serial      = "".join(random.choices(string.digits, k=6))
    correct     = compute_check_digit(prefix[:3], prefix[3], serial)
    wrong       = (correct + random.randint(1, 9)) % 10
    return f"{prefix}{serial}{wrong}"


def make_invalid_format_id() -> str:
    """Generate a malformed string that won't match the container ID regex."""
    variants = [
        f"AB{''.join(random.choices(string.digits, k=7))}",   # only 2 letters
        f"ABCD{''.join(random.choices(string.digits, k=5))}",  # 5 digits instead of 7
        f"1234{''.join(random.choices(string.digits, k=7))}",  # starts with digits
    ]
    return random.choice(variants)


# ---------------------------------------------------------------------------
# Mock Data Generation
# ---------------------------------------------------------------------------

def make_mock_data() -> dict:
    """Generate realistic mock data for the manifest fields based on real-world global logistics."""
    
    # Top global container shipping lines
    carriers = [
        "MSC (Mediterranean Shipping Company)", "Maersk Line", "CMA CGM Group", 
        "COSCO Shipping Lines", "Hapag-Lloyd", "Ocean Network Express (ONE)", 
        "Evergreen Line", "Yang Ming Marine Transport", "ZIM Integrated Shipping", 
        "HMM (Hyundai Merchant Marine)", "Wan Hai Lines", "OOCL"
    ]
    
    # Major global container ports
    ports = [
        "Port of Shanghai, CN", "Port of Singapore, SG", "Port of Ningbo-Zhoushan, CN", 
        "Port of Shenzhen, CN", "Port of Qingdao, CN", "Port of Guangzhou, CN", 
        "Port of Busan, KR", "Port of Tianjin, CN", "Port of Jebel Ali, AE", 
        "Port of Rotterdam, NL", "Port of Los Angeles, US", "Port of Long Beach, US", 
        "Port of New York/New Jersey, US", "Port of Antwerp-Bruges, BE", "Port of Hamburg, DE"
    ]
    
    # Realistic sounding government/military units (Standard Form 245 is often US Gov/Mil)
    units = [
        "Defense Logistics Agency (DLA)", "Military Sealift Command (MSC)", 
        "Naval Supply Systems Command (NAVSUP)", "U.S. Transportation Command (USTRANSCOM)", 
        "Surface Deployment and Distribution Command", "1st Marine Logistics Group"
    ]
    
    # Realistic sounding operations/projects
    projects = [
        "Operation Pacific Resolve", "Logistics Support 2026", "Task Force Enduring", 
        "Exercise Iron Shield", "Joint Strike Delta", "Global Sentinel"
    ]
    
    # Realistic ship names (trans_id) and captains
    ships = [
        "MSC Gulsun (IMO: 9839430)", "Madrid Maersk (IMO: 9778791)", 
        "CMA CGM Jacques Saade (IMO: 9839179)", "OOCL Hong Kong (IMO: 9776171)", 
        "Ever Given (IMO: 9811000)", "HMM Algeciras (IMO: 9863297)"
    ]
    
    captains = ["Capt. L. Sterling", "Capt. J. Miller", "Master M. O'Brian", "Capt. A. Chen", "Capt. S. Rahman", "Master B. Ivanov"]
    
    departure = random.choice(ports)
    # Pick a destination port that isn't the departure
    destination = random.choice([p for p in ports if p != departure])
    
    return {
        "ordering_unit": random.choice(units),
        "project_name": random.choice(projects),
        "project_no": f"PROJ-{random.choice(['ALPHA', 'BETA', 'GAMMA', 'DELTA'])}-{random.randint(100, 999)}",
        "carrier": random.choice(carriers),
        "trans_mode_id": random.choice(ships),
        "driver": random.choice(captains),
        "chief_of_party": random.choice(["LCDR T. Vance", "Col. R. Decker", "Director M. Sato", "Cmdr. E. Thorne"]),
        "delayed_contact": f"+1 ({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
        "dep_place": departure,
        "dep_etd": f"2026-03-{random.randint(10, 20):02d} {random.randint(6, 11):02d}:00Z",
        "dep_eta": f"2026-03-{random.randint(1, 9):02d} {random.randint(1, 15):02d}:30Z",
        "int_place": "NONE / DIRECT",
        "int_etd": "N/A",
        "dest_place": destination,
        "dest_eta": f"2026-04-{random.randint(1, 28):02d} {random.randint(12, 23):02d}:00Z",
    }


# ---------------------------------------------------------------------------
# PDF/Image generation
# ---------------------------------------------------------------------------

def stamp_pdf(container_id: str | list[str], out_path: Path, label: str = "", output_format: str = "pdf", augment: bool = False) -> None:
    """
    Open template.pdf, write mock data and container_ids text, save to out_path.
    If output_format is 'png', renders the page as a high-res image and saves it.
    """
    doc  = fitz.open(str(TEMPLATE_PDF))
    page = doc[0]

    # Delete all interactive form widgets so PDF readers don't show the blue highlight boxes
    for widget in page.widgets():
        page.delete_widget(widget)

    font_name = "courier-bold"
    font_size = 10
    color     = (0, 0, 0)
    
    mock = make_mock_data()

    # Exact coordinates mapped to the template fields (X aligned left, Y shifted down into the blue boxes)
    fields = [
        # Field name,         Text string,          X,   Y,   W,   H  (fitz top-left origin, Y adjusted up ~8pt for textbox top border)
        ("Ordering Unit",     mock["ordering_unit"],    35,  64,  150, 30),
        ("Project Name",      mock["project_name"],     195, 64,  205, 30),
        ("Project No.",       mock["project_no"],       410, 64,  150, 30),
        
        ("Name of Carrier",   mock["carrier"],          35,  97,  150, 30),
        ("Mode of Trans",     mock["trans_mode_id"],    195, 97,  205, 30),
        ("Pilot or Driver",   mock["driver"],           410, 97,  150, 30),
        
        ("Chief of Party",    mock["chief_of_party"],   195, 132, 205, 30), # Below REPORT TO
        ("Contact if Delayed",mock["delayed_contact"],  410, 132, 150, 30),
        
        ("Departure Place",   mock["dep_place"],        35,  187, 110, 30),
        ("Departure ETD",     mock["dep_etd"],          155, 187, 42,  30),
        ("Departure ETA",     mock["dep_eta"],          200, 187, 42,  30),
        
        ("Intermediate Place",mock["int_place"],        245, 187, 115, 30),
        ("Intermediate ETD",  mock["int_etd"],          370, 187, 42,  30),
        
        ("Dest ETA",          mock["dest_eta"],         420, 187, 42,  30),
        ("Dest Place",        mock["dest_place"],       465, 187, 110, 30),
    ]

    for name, text, x_base, y_base, w, h in fields:
        # Add slight randomization to simulate typing/printing variation
        # X: jitter slightly left, or up to 10 points right
        # Y: jitter up to 4 points up or 6 points down
        x = x_base + random.uniform(-2, 10)
        y = y_base + random.uniform(-4, 6)
        
        rect = fitz.Rect(x, y, x + w, y + h)
        # Use insert_textbox so it automatically wraps if it hits the width limit!
        page.insert_textbox(rect, text, fontname=font_name, fontsize=font_size, color=color)

    # --- Container IDs in the Cargo Name table ---
    # First row, passenger/cargo name column starts around X=60, Y=250.5
    # Each row is approximately 21.6 points tall
    cid_font_size = 14
    cid_x_base = 70
    cid_y_base = 250.5
    row_height = 21.6 # Exact row height extracted from template PDF numbering
    
    # We expect container_id to be a list or tuple now. If string, wrap in list.
    if isinstance(container_id, str):
        container_ids = [container_id]
    else:
        container_ids = container_id

    for row_idx, cid in enumerate(container_ids):
        current_y_base = cid_y_base + (row_idx * row_height)
        
        cid_x = cid_x_base + random.uniform(-2, 10)
        cid_y = current_y_base + random.uniform(-1, 2)
        
        page.insert_text(
            (cid_x, cid_y),
            cid,
            fontname="courier-bold",
            fontsize=cid_font_size,
            color=(0, 0, 0),
        )

        # Cargo details (Weight, M/F/Duty) just to fill the row out realistically
        f_x = 242 + random.uniform(0, 4) # M/F column
        pw_x = 265 + random.uniform(0, 4) # Passenger Weight column
        cw_x = 315 + random.uniform(0, 4) # Cargo Weight column
        d_x = 375 + random.uniform(0, 4) # Duty Assignment column
        y_cargo = current_y_base + random.uniform(-1, 2)

        # Insert '-' for passenger columns since it is a cargo container
        page.insert_text((f_x, y_cargo), "-", fontname="helv", fontsize=10)
        page.insert_text((pw_x, y_cargo), "-", fontname="helv", fontsize=10)
        page.insert_text((cw_x, y_cargo), f"{random.randint(1000, 9000)} KG", fontname="helv", fontsize=10)
        page.insert_text((d_x, y_cargo), "CARGO", fontname="helv", fontsize=10)
    
    # --- small label below (variant info) ---
    if label:
        x_centre  = page.rect.width / 2
        label_size  = 11
        label_width = fitz.get_text_length(label, fontname="helv", fontsize=label_size)
        lx = x_centre - label_width / 2
        page.insert_text(
            (lx, 740),  # bottom margin
            label,
            fontname="helv",
            fontsize=label_size,
            color=(0.4, 0.4, 0.4),
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_format == "png":
        # Render at 300 DPI (approx 4.16 scale factor relative to 72 DPI base)
        mat = fitz.Matrix(4.16, 4.16)
        pix = page.get_pixmap(matrix=mat)
        
        if augment and cv2 is not None and np is not None:
            # Convert PyMuPDF pixmap to numpy array
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            
            # Need to make a writable copy since frombuffer returns read-only memoryview
            img_array = np.copy(img_array)
            
            if pix.n == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            elif pix.n == 4: # RGBA -> BGRA
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
                
            img_array = augment_image(img_array)
            cv2.imwrite(str(out_path), img_array)
        else:
            pix.save(str(out_path))
    else:
        # Saving as PDF
        doc.save(str(out_path))
        
    doc.close()


# ---------------------------------------------------------------------------
# Batch generation
# ---------------------------------------------------------------------------

def generate_batch(count: int, out_dir: Path, output_format: str = "pdf", augment: bool = False) -> list[Path]:
    """Generate 'count' valid + 2 invalid-checkdigit + 1 invalid-format files."""
    generated: list[Path] = []
    
    ext = output_format

    # Valid IDs - generate a list of IDs instead of just one
    for i in range(1, count + 1):
        # Randomize how many cargo rows to fill (1 to 15 max)
        num_rows = random.randint(1, 15)
        cids = [make_valid_container_id() for _ in range(num_rows)]
        
        path = out_dir / f"valid_{i}_{num_rows}rows.{ext}"
        stamp_pdf(cids, path, label=f"VALID | {num_rows} entries | #{i}", output_format=output_format, augment=augment)
        
        # Determine the id string for printing based on list size
        print_id = cids[0] if len(cids) == 1 else f"{cids[0]} (+{len(cids)-1} more)"
        print(f"  [VALID]           {path.name}  ->  {print_id}")
        generated.append(path)

    # Invalid check digit
    for i in range(1, 3):
        cid  = make_invalid_checkdigit_id()
        path = out_dir / f"invalid_checkdigit_{i}.{ext}"
        stamp_pdf(cid, path, label=f"INVALID | wrong check digit | #{i}", output_format=output_format, augment=augment)
        print(f"  [INVALID-DIGIT]   {path.name}  ->  {cid}")
        generated.append(path)

    # Invalid format (won't be found by regex at all)
    cid  = make_invalid_format_id()
    path = out_dir / f"invalid_format_1.{ext}"
    stamp_pdf(cid, path, label="INVALID FORMAT | no regex match expected", output_format=output_format, augment=augment)
    print(f"  [INVALID-FORMAT]  {path.name}  ->  {cid}")
    generated.append(path)

    return generated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate test PDFs for Ayahay SmartScan OCR validation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--id",
        metavar="CONTAINER_ID",
        help="Stamp a single specific container ID (e.g. MSCU1234568).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        metavar="N",
        help="Number of valid test PDFs to generate in batch mode (default: 3).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT,
        metavar="DIR",
        help=f"Output directory (default: {DEFAULT_OUT}).",
    )
    parser.add_argument(
        "--image",
        action="store_true",
        help="Export the generated documents as high-res PNG images instead of PDFs.",
    )
    parser.add_argument(
        "--augment",
        action="store_true",
        help="Apply realistic physical degradations (blur, rips, spills) to output images. Implies --image.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available container owner-code prefixes and exit.",
    )
    args = parser.parse_args()

    # --list
    if args.list:
        print("Available prefixes:")
        for p in PREFIXES:
            print(f"  {p}")
        return

    # Validate template exists
    if not TEMPLATE_PDF.exists():
        print(f"ERROR: template not found at {TEMPLATE_PDF}")
        print("       Place your blank template PDF at docs/template.pdf")
        sys.exit(1)

    if args.augment:
        args.image = True

    output_format = "png" if args.image else "pdf"

    print("=" * 60)
    print("Ayahay SmartScan - Test Data Generator")
    print("=" * 60)
    print(f"Template:   {TEMPLATE_PDF}")
    print(f"Output dir: {args.output}")
    print(f"Format:     {output_format.upper()}{' (Augmented)' if args.augment else ''}")
    print("-" * 60)

    # --id: single custom PDF
    if args.id:
        cid      = args.id.upper().replace(" ", "").replace("-", "")
        out_path = args.output / f"custom_{cid}.{output_format}"
        stamp_pdf(cid, out_path, label=f"CUSTOM | {args.id}", output_format=output_format, augment=args.augment)
        print(f"  [CUSTOM]  {out_path.name}  ->  {cid}")
    else:
        generate_batch(args.count, args.output, output_format=output_format, augment=args.augment)

    print("-" * 60)
    print(f"Done! Files saved to: {args.output.resolve()}")
    print()
    print("To test with the OCR engine:")
    print(f"  py test_ocr.py \"{args.output / f'valid_1_*.{output_format}'}\"")
    print("=" * 60)


if __name__ == "__main__":
    main()

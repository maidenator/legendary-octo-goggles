"""
test_ocr.py — Test the ContainerOCREngine against any PDF or image file.

Usage:
    py test_ocr.py <path/to/file.pdf>
    py test_ocr.py <path/to/image.jpg>
"""

import sys
from pathlib import Path
from ocr_engine import ContainerOCREngine


def run_test(file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File not found: {path.resolve()}")
        sys.exit(1)

    print("=" * 60)
    print("Ayahay SmartScan - OCR Engine Test")
    print("=" * 60)
    print(f"File:     {path.resolve()}")
    print(f"Type:     {path.suffix.upper() or 'unknown'}")
    print("-" * 60)

    engine = ContainerOCREngine()
    result = engine.process(path)

    print(f"\nRaw text (first 400 chars):")
    print("-" * 60)
    print((result["raw_text"] or "[empty]")[:400])
    print("-" * 60)

    ids = result["container_ids_found"]
    print(f"\nContainer IDs found ({len(ids)}):")
    if ids:
        for cid in ids:
            print(f"  {cid}")
    else:
        print("  [none]")

    print(f"\nValidation results:")
    for v in result["validated_ids"]:
        status = "VALID" if v["valid"] else "INVALID"
        detail = f"  (check digit: {v['check_digit']})" if v["valid"] else f"  ({v['error']})"
        print(f"  [{status}] {v['container_id']}{detail}")

    print(f"\n{'='*60}")
    if result["best_match"]:
        print(f"BEST MATCH: {result['best_match']['container_id']}")
    elif result["error"]:
        print(f"NO VALID ID: {result['error']}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py test_ocr.py <path/to/file.pdf or image.jpg>")
        print("Example: py test_ocr.py ..\\docs\\template.pdf")
        sys.exit(1)
    run_test(sys.argv[1])

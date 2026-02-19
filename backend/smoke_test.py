"""Capture test_ocr.py output by importing directly."""
import sys, io
from pathlib import Path

# Redirect stdout to capture
buf = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buf

# Run test inline
from ocr_engine import ContainerOCREngine
import cv2, numpy as np

# Create a synthetic image with container text
img = 255 * np.ones((400, 800, 3), dtype="uint8")
cv2.putText(img, "MSCU 123456-7", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 0), 4)
cv2.imwrite("smoke_test.jpg", img)

engine = ContainerOCREngine()
result = engine.process(Path("smoke_test.jpg"))

sys.stdout = old_stdout
Path("smoke_test.jpg").unlink(missing_ok=True)

print("=" * 60)
print("Ayahay SmartScan - OCR Engine Smoke Test")
print("=" * 60)
print(f"Raw text:           {repr((result['raw_text'] or '').strip()[:200])}")
print(f"IDs found:          {result['container_ids_found']}")
print(f"Validated IDs:      {[(v['container_id'], 'VALID' if v['valid'] else v['error']) for v in result['validated_ids']]}")
print(f"Best match:         {result['best_match']['container_id'] if result['best_match'] else None}")
print(f"Error:              {result['error']}")
print("=" * 60)
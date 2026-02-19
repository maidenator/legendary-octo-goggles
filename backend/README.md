# Ayahay SmartScan - Backend Setup

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR Binary

**⚠️ IMPORTANT:** PyTesseract requires the Tesseract OCR binary installed separately.

#### Windows:
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Or use Chocolatey: `choco install tesseract`
- After installation, verify: `tesseract --version`

#### Linux (Debian/Ubuntu):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### macOS:
```bash
brew install tesseract
```

### 3. Test OCR Engine (Optional)

Test the OCR engine with a sample image:

```bash
python test_ocr.py path/to/image.jpg
```

### 4. Run the Server

```bash
python main.py
```

The server will start on `http://0.0.0.0:8000` (accessible from mobile devices on the same network).

## API Endpoints

- `GET /` - Health check
- `GET /health` - Health check
- `POST /scan` - Upload image for OCR processing

## Testing the Full Flow

1. Start the server: `python main.py`
2. Open `frontend/index.html` in a browser
3. Scan an image with container IDs
4. Click "Send to Server"
5. Check server console for OCR results
6. Check browser console for API response

## Troubleshooting

### Tesseract Not Found
If you get `TesseractNotFoundError`:
- Make sure Tesseract binary is installed
- On Windows, you may need to add Tesseract to PATH or set:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### OCR Not Finding Container IDs
- Ensure image quality is good (clear text, good contrast)
- Container IDs must match format: `ABCD1234567` (4 letters + 7 digits)
- Try adjusting image preprocessing in `ocr_engine.py`

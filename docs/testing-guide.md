# Testing Guide - Ayahay SmartScan

## Prerequisites

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Tesseract OCR Binary

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Or: `choco install tesseract`
- Verify: `tesseract --version` in Command Prompt

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

## Testing Methods

### Method 1: Test OCR Engine Directly

Test the OCR engine with a sample image:

```bash
cd backend
python test_ocr.py path/to/image.jpg
```

**Example:**
```bash
python test_ocr.py uploads/scan_20240219_123456.jpg
python test_ocr.py ../test_images/container_manifest.jpg
```

**What to expect:**
- Extracted text from image
- List of container IDs found
- Validation results for each ID
- Best match (first valid container ID)

### Method 2: Test Full Server Integration

1. **Start the FastAPI server:**
   ```bash
   cd backend
   python main.py
   ```
   
   You should see:
   ```
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Test with curl (optional):**
   ```bash
   curl -X POST "http://localhost:8000/scan" \
     -F "file=@path/to/image.jpg"
   ```

3. **Test with Frontend:**
   - Open `frontend/index.html` in a browser
   - Scan an image or select a file
   - Click "Send to Server"
   - Check browser console for response
   - Check server console for OCR processing logs

### Method 3: Test API Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Root Endpoint:**
```bash
curl http://localhost:8000/
```

**Scan Endpoint:**
```bash
curl -X POST "http://localhost:8000/scan" \
  -F "file=@test_image.jpg" \
  -H "Content-Type: multipart/form-data"
```

## Expected Results

### Successful OCR Processing

**Server Console:**
```
[INFO] Received image: test.jpg
[INFO] Saved as: scan_20240219_123456.jpg
[INFO] File size: 245760 bytes (240.00 KB)
[INFO] Processing image with OCR engine...
[INFO] Container ID found: ABCD1234567 (Status: valid)
```

**API Response:**
```json
{
  "success": true,
  "message": "Image processed successfully",
  "filename": "scan_20240219_123456.jpg",
  "size_bytes": 245760,
  "size_kb": 240.0,
  "timestamp": "20240219_123456",
  "ocr_result": {
    "container_id": "ABCD1234567",
    "validation_status": "valid",
    "container_ids_found": ["ABCD1234567"],
    "raw_text_preview": "CONTAINER ID: ABCD1234567...",
    "error": null
  }
}
```

### No Container IDs Found

**API Response:**
```json
{
  "ocr_result": {
    "container_id": null,
    "validation_status": null,
    "container_ids_found": [],
    "raw_text_preview": "Some text from image...",
    "error": "No container IDs found in image"
  }
}
```

## Troubleshooting

### Issue: TesseractNotFoundError

**Solution:**
- Verify Tesseract is installed: `tesseract --version`
- On Windows, check if path is set correctly in `ocr_engine.py`
- Add Tesseract to system PATH or update `ocr_engine.py` with correct path

### Issue: No Container IDs Found

**Possible causes:**
- Image quality too low
- Text not clear/readable
- Container ID format doesn't match `[A-Z]{4}\d{7}`
- Image preprocessing needs adjustment

**Solutions:**
- Use higher quality images
- Ensure good lighting and contrast
- Check that container IDs match format: 4 letters + 7 digits
- Try adjusting preprocessing parameters in `ocr_engine.py`

### Issue: Container ID Found But Invalid

**Possible causes:**
- OCR misread characters (e.g., 0 vs O, 1 vs I)
- Check digit validation failed
- Container ID doesn't exist

**Solutions:**
- Improve image quality
- Check OCR extracted text for errors
- Verify container ID format manually

### Issue: Server Won't Start

**Check:**
- All dependencies installed: `pip list`
- Port 8000 not in use: `netstat -an | findstr 8000` (Windows)
- Python version: `python --version` (should be 3.10+)

## Test Images

For testing, you can:
1. Take a photo of a container manifest
2. Use a sample image with text containing container IDs
3. Create a test image with text: "CONTAINER ID: ABCD1234567"

**Note:** Container IDs must match ISO 6346 format (4 uppercase letters + 7 digits with valid check digit).

## Next Steps

After successful testing:
- Proceed to Module 4 (Database) for persistent storage
- Optimize OCR preprocessing if needed
- Add error handling improvements
- Test with real-world images from the pier

"""
Ayahay SmartScan - FastAPI Server (Traffic Cop)
Receives compressed images from the mobile PWA and routes them to the OCR engine.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path
import os
from datetime import datetime
from ocr_engine import process_image
from database import init_db, save_scan, get_scans, get_scan_by_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Ayahay SmartScan API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware to allow requests from the mobile PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=False,  # Must be False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "status": "online",
        "service": "Ayahay SmartScan API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/scan")
async def scan_image(file: UploadFile = File(...)):
    """
    Receive compressed image from mobile PWA, run OCR, and save result to DB.

    Steps:
    1. Validate file type (must be image/*)
    2. Save file to uploads/ with timestamped name
    3. Process with OCR engine (Module 3)
    4. Persist result to SQLite (Module 4)
    5. Return full result JSON
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(file.filename).suffix or ".jpg"
        saved_filename = f"scan_{timestamp}{file_extension}"
        file_path = UPLOAD_DIR / saved_filename

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        file_size = len(content)

        # Log receipt
        print(f"[INFO] Received image: {file.filename}")
        print(f"[INFO] Saved as: {saved_filename}")
        print(f"[INFO] File size: {file_size} bytes ({file_size / 1024:.2f} KB)")

        # Save a debug copy to see exactly what the frontend Javascript is passing us
        import shutil
        shutil.copyfile(file_path, UPLOAD_DIR / "debug_received.jpg")

        # Module 3 — Process with OCR engine
        print(f"[INFO] Processing image with OCR engine...")
        ocr_result = process_image(file_path)

        # Extract results
        container_id = None
        validation_status = None

        if ocr_result['success'] and ocr_result['best_match']:
            container_id = ocr_result['best_match']['container_id']
            validation_status = "valid" if ocr_result['best_match']['valid'] else "invalid"
            print(f"[INFO] Container ID found: {container_id} (Status: {validation_status})")
        else:
            print(f"[WARN] OCR processing failed or no valid container ID found")
            if ocr_result.get('error'):
                print(f"[WARN] Error: {ocr_result['error']}")

        # Module 4 — Persist result to database
        raw_preview = ocr_result.get('raw_text', '')[:200] if ocr_result.get('raw_text') else None
        scan_id = save_scan(
            filename=saved_filename,
            size_bytes=file_size,
            timestamp=timestamp,
            container_id=container_id,
            validation_status=validation_status,
            raw_text_preview=raw_preview,
            error=ocr_result.get('error'),
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Image processed successfully",
                "scan_id": scan_id,
                "filename": saved_filename,
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2),
                "timestamp": timestamp,
                "ocr_result": {
                    "container_id": container_id,
                    "validation_status": validation_status,
                    "container_ids_found": ocr_result.get('container_ids_found', []),
                    "raw_text_preview": raw_preview,
                    "error": ocr_result.get('error')
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to process image: {str(e)})")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )


@app.get("/scans")
async def list_scans(limit: int = 50):
    """
    Retrieve the most recent scan records from the database.

    Query params:
        limit: Max number of records to return (default 50, max 500).
    """
    limit = min(limit, 500)  # cap to prevent huge responses
    records = get_scans(limit=limit)
    return {
        "count": len(records),
        "scans": records,
    }


@app.get("/scans/{scan_id}")
async def get_scan(scan_id: int):
    """Retrieve a single scan record by ID."""
    record = get_scan_by_id(scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    return record


if __name__ == "__main__":
    # Run server on localhost, accessible from mobile device on same network
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Listen on all interfaces for mobile access
        port=8000,
        reload=debug_mode  # Only auto-reload in debug mode
    )

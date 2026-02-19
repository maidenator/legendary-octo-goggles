"""
Ayahay SmartScan - FastAPI Server (Traffic Cop)
Receives compressed images from the mobile PWA and routes them to the OCR engine.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path
import os
from datetime import datetime
from ocr_engine import process_image

app = FastAPI(title="Ayahay SmartScan API", version="1.0.0")

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
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Ayahay SmartScan API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/scan")
async def scan_image(file: UploadFile = File(...)):
    """
    Receive compressed image from mobile PWA and process it.
    
    This endpoint:
    1. Receives the compressed JPEG image
    2. Saves it temporarily
    3. Will route to OCR engine (Module 3)
    4. Will save results to database (Module 4)
    
    For now, just confirms receipt and returns file info.
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
        
        # Module 3 - Process with OCR engine
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
        
        # TODO: Module 4 - Save results to database
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Image processed successfully",
                "filename": saved_filename,
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2),
                "timestamp": timestamp,
                "ocr_result": {
                    "container_id": container_id,
                    "validation_status": validation_status,
                    "container_ids_found": ocr_result.get('container_ids_found', []),
                    "raw_text_preview": ocr_result.get('raw_text', '')[:200] if ocr_result.get('raw_text') else None,
                    "error": ocr_result.get('error')
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to process image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )


if __name__ == "__main__":
    # Run server on localhost, accessible from mobile device on same network
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Listen on all interfaces for mobile access
        port=8000,
        reload=True  # Auto-reload on code changes
    )

# API Reference

The Ayahay SmartScan backend is powered by FastAPI. By default, it runs on http://localhost:8000.

## Endpoints

### 1. Scan Image
Processes an uploaded image/PDF through the OCR pipeline.

- **URL**: /scan
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Body**: 
  - `file`: The image or PDF file to scan.
- **Success Response**:
  ```json
  {
    "success": true,
    "best_match": {
      "container_id": "TCKU7336934",
      "valid": true,
      "check_digit": 4
    },
    "validated_ids": [...]
  }
  ```

### 2. Get Scan History
Retrieves the history of all processed scans from the SQLite database.

- **URL**: /scans
- **Method**: GET
- **Parameters**:
  - `limit`: (Optional) Max number of records to return. Default: 100.
- **JSON Structure**:
  ```json
  [
    {
      "id": 1,
      "timestamp": "2026-02-20T08:00:00",
      "filename": "manifest_01.jpg",
      "status": "valid",
      "container_id": "TCKU7336934"
    }
  ]
  ```

## WebSocket Support
(Planned for Future Version): Real-time scan updates to connected clients.

## Module 2 – FastAPI Server (Traffic Cop)

**Purpose:** Receive compressed images from the PWA, persist them, and later orchestrate OCR + validation + storage.

### Tech & Files

- **Stack:** Python 3.10+, FastAPI, Uvicorn.
- **Files:**
  - `backend/main.py` – FastAPI app.
  - `backend/requirements.txt` – dependencies.
  - `backend/.gitignore` – excludes Python artifacts and uploads.
  - Upload directory: `backend/uploads/` (created at runtime).

### App Setup (`main.py`)

- `FastAPI(title="Ayahay SmartScan API", version="1.0.0")`.
- CORS:
  - `allow_origins=["*"]` for hackathon simplicity (tighten later).
  - All methods and headers allowed.
- Upload directory:
  - `UPLOAD_DIR = Path("uploads")` (relative to `backend/` when run there).
  - `UPLOAD_DIR.mkdir(exist_ok=True)`.

### Endpoints

- `GET /`
  - Basic health/meta:
    - `{ "status": "online", "service": "Ayahay SmartScan API", "version": "1.0.0" }`.

- `GET /health`
  - Simple `{ "status": "healthy" }`.

- `POST /scan`
  - **Input:** `file: UploadFile = File(...)` (multipart/form-data from the PWA).
  - **Validation:** `content_type` must start with `"image/"`.
  - **Processing (current):**
    - Generate timestamped filename: `scan_YYYYMMDD_HHMMSS.ext`.
    - Save raw bytes into `uploads/`.
    - Log file name and size.
  - **Response (current):**
    - `success: true`, `filename`, `size_bytes`, `size_kb`, `timestamp`.
    - Placeholders: `container_id: null`, `validation_status: null`.
  - **Future:**
    - Call OCR engine (Module 3) on `file_path`.
    - Persist result + metadata to SQLite (Module 4).

### Running the Server

From the `backend/` directory:

```bash
pip install -r requirements.txt
python main.py
```

- Runs via `uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)`.
- `0.0.0.0` allows other devices on the same LAN (e.g., pier Wi‑Fi) to reach the API.

### Frontend → Backend Contract

- **URL:** `http://<server-ip>:8000/scan` (default in PWA is `http://localhost:8000`).
- **Method:** `POST`.
- **Content-Type:** `multipart/form-data`.
- **Field name:** `file` (the compressed JPEG from `app.js`).

The server currently only confirms receipt and size; OCR and validation will plug in here in Modules 3 and 4.


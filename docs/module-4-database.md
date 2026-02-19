## Module 4 – Database (SQLite)

**Purpose:** Persist every OCR scan result to a local SQLite file so records survive server restarts and can be reviewed by the clerk.

### Tech & Files

- **Stack:** Python built-in `sqlite3` — no extra dependencies.
- **Files:**
  - `backend/database.py` – all DB logic (init, save, query).
  - `backend/smartscan.db` – auto-created SQLite file (gitignored).

### Schema

```sql
CREATE TABLE IF NOT EXISTS scans (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    filename           TEXT    NOT NULL,
    size_bytes         INTEGER,
    timestamp          TEXT,
    container_id       TEXT,
    validation_status  TEXT,      -- 'valid', 'invalid', or NULL
    raw_text_preview   TEXT,      -- first 200 chars of OCR output
    error              TEXT,      -- error message if OCR failed
    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Functions (`database.py`)

| Function | Description |
|----------|-------------|
| `init_db()` | Creates `scans` table if not exists. Called once at server startup. |
| `save_scan(...)` | Inserts a scan record. Returns the new row `id`. |
| `get_scans(limit)` | Returns up to `limit` records, newest first. Default 50. |
| `get_scan_by_id(id)` | Returns a single record dict or `None`. |

### New API Endpoints

- **`GET /scans?limit=50`** — List recent scans as JSON array.
- **`GET /scans/{id}`** — Get a specific scan record by ID.
- **`POST /scan`** — Now also returns `scan_id` in the response.

### Running

No changes to startup command — the DB file is created automatically:

```bash
cd backend
python main.py
```

After a scan:
```bash
# List all scans
curl http://localhost:8000/scans

# Get a specific scan
curl http://localhost:8000/scans/1
```

### Data Flow

```
Phone (PWA)
    │  POST /scan (JPEG)
    ▼
main.py  ──►  ocr_engine.py  ──►  Tesseract OCR
    │
    ▼
database.py  ──►  smartscan.db  (SQLite)
    │
    ▼
GET /scans  (query history)
```

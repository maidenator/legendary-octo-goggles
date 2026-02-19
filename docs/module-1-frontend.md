## Module 1 – Phone Scanner (Frontend)

**Purpose:** Mobile-first PWA that captures a manifest photo, compresses it on-device, shows a preview, and sends it to the FastAPI backend.

### Tech & Files

- **Stack:** Vanilla JS, HTML5 `<input capture>`, Canvas, Tailwind CSS (CDN).
- **Files:**
  - `frontend/index.html` – UI shell and camera input.
  - `frontend/app.js` – image handling, compression, upload logic.
  - `frontend/manifest.json` – basic PWA manifest.

### UX Flow

1. **Landing UI (`index.html`):**
   - Mobile-first layout with Tailwind.
   - Prominent “Tap to Scan” card.
   - Hidden file input:
     - `type="file"`, `accept="image/*"`, `capture="environment"`.
2. **Capture:**
   - Tapping the card triggers the hidden input.
   - On mobile, this opens the back camera (where supported).

### Compression Pipeline (`app.js`)

- Listen for `change` on `#camera-input`.
- Read the selected file via `FileReader.readAsDataURL`.
- Create an `Image` from the data URL.
- Draw onto an invisible `<canvas>`:
  - Max width: **1500 px**.
  - Preserve aspect ratio by scaling height.
- Export with `canvas.toBlob(…, 'image/jpeg', 0.8)`:
  - **JPEG quality:** `0.8` (80%).
  - Wrap blob as `compressedFile = new File([...], originalName, { type: 'image/jpeg' })`.

### Preview & Status

- Preview:
  - `URL.createObjectURL(blob)` → `#preview-image.src`.
  - Show `#preview-section`.
- File size info:
  - Show original vs compressed size and % reduction.
- Status:
  - `showStatus(message, cssColorClass)` updates `#status-message`.

### Upload to Backend

- **Trigger:** “Send to Server” button (`#send-button`).
- Disabled and label changed to “Sending…” during upload.
- Request:
  - `FormData` with `formData.append('file', compressedFile)`.
  - `fetch(`${serverUrl}/scan`, { method: 'POST', body: formData })`.
  - `serverUrl` defaults to `http://localhost:8000` (can override via `window.SERVER_URL`).
- Response handling:
  - On `200 OK`, parse JSON and show success message including `size_bytes`.
  - On error, show error message and re-enable button.


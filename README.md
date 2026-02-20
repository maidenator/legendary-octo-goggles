# 🚢 Ayahay SmartScan

**Ayahay SmartScan** is a high-precision OCR engine and web dashboard designed specifically for identifying and validating maritime shipping container IDs (ISO 6346) from camera scans and documents.

[![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20OpenCV%20%7C%20Tesseract-blue)](https://github.com/maidenator/legendary-octo-goggles)

## ✨ Features
- **Smart OCR Brain**: Uses Bilateral Filtering and Adaptive Thresholding to read text from noisy, crumpled, or stained documents.
- **Fuzzy ID Repair**: Brute-forces common OCR misreadings (e.g., `S` vs `5`, `O` vs `0`) to maximize valid ID recovery.
- **Validation**: Strict ISO 6346 check-digit verification.
- **Web Dashboard**: Real-time scan history with status badges and searchable records.
- **Mock Data Generator**: Generate realistic augmented PDF/PNG test data for pipeline stress testing.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed on your system.

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run the Backend (API)
```bash
cd backend
python main.py
```

### 4. Run the Frontend (UI)
```bash
cd frontend
python -m http.server 8001
```
Open [http://localhost:8001](http://localhost:8001) in your browser.

## 🛠️ Technical Documentation
- [System Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Testing & Mock Data](docs/testing-guide.md)

---
*Created with 💙 for the logistics industry.*
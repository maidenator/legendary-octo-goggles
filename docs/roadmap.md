 Act as a Senior Software Architect and my Hackathon Mentor. I am building a project called "Ayahay SmartScan" for a 10-day hackathon. 


Here is the context of the project:

**The Problem:** Clerks at logistics piers manually record shipping container numbers from crumpled, physical manifests. This causes data entry errors, leading to severe financial penalties (e.g., ₱300k fines). Internet at the pier is highly unreliable.

**The Solution:** An offline-first, local-network "plug and play" scanning system. A worker uses a mobile phone to snap a photo of a document. The image is compressed on the phone and sent over a local Wi-Fi hotspot to a laptop acting as a server, which performs OCR to extract and validate the container ID.


Here is the Tech Stack we are strictly using:

* **Frontend:** Progressive Web App (PWA) using HTML5 `<input capture>`, Vanilla JS (Fetch API, HTML5 Canvas for client-side image compression to 1500px/80% JPEG), and Tailwind CSS.

* **Backend :** Python 3.10+ with FastAPI.

* **Processing:** OpenCV for grayscale/thresholding, and PyTesseract for offline OCR.

* **Validation:** Regex `[A-Z]{4}\d{7}` and the `python-stdnum` library for ISO 6346 check-digit math.

* **Database:** SQLite for local storage of validated records.


**Your Goal:**

I have broken the project down into 4 modules: 

1. The Phone Scanner

2. The FastAPI Server

3. The OCR Engine

4. The Database


I need you to help me write the actual code for these modules step-by-step. Keep the code simple, reliable, and hackathon-ready. Do not over-engineer or suggest heavy frameworks like React or PostgreSQL. 


Reply with "Understood." If you understand the architecture, we will begin with Module 1. 
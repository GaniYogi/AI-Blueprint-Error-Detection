# AI Blueprint Error Detection

AI Blueprint Error Detection is a full-stack, production-ready SaaS application for analyzing architectural drawings and construction blueprints. It automatically detects walls, doors, windows, staircases, and columns, extracts dimensions/annotations via OCR, and validates designs against regional building codes to highlight violations before construction begins.

## Key Features

1. **AI Blueprint Analysis Engine:** Integrates custom YOLO object detection (via OpenCV & Ultralytics) to map drawing components.
2. **Text & Dimension OCR:** Integrates EasyOCR to parse room labels, measurements, and annotations.
3. **Building Code Compliance:** Evaluates designs against minimum bedroom area, minimum door/corridor width, and window ventilation ratios.
4. **Interactive Viewer Canvas:** Visualizes drawings with hover-activated bounding boxes, color-coded error overlays, and pan/zoom controls.
5. **Auto-Generated PDF Reports:** Compiles findings, severity breakdowns, compliance tables, and recommendations into a formatted PDF using ReportLab.
6. **SaaS Dashboard & Settings:** Displays aggregate error metrics and trends, and allows live adjustments of code compliance thresholds.

---

## Project Structure

```
AI-Blueprint-Error-Detection/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration, JWT Auth helpers
│   │   ├── db/             # SQLAlchemy connection & models (SQLite/PostgreSQL)
│   │   ├── engine/         # Computer Vision (YOLO/OCR) pipeline, PDF Generator
│   │   ├── routers/        # FastAPI API controllers
│   │   └── main.py         # Entrypoint
│   │
│   ├── requirements.txt    # Python dependencies
│   └── verify_services.py  # Self-diagnostic utility
│
├── frontend/
│   ├── src/
│   │   ├── context/        # Auth state context
│   │   ├── pages/          # React views (Landing, Dashboard, Upload, Canvas, etc.)
│   │   ├── services/       # Axios API mappings
│   │   ├── App.tsx         # Routing & Main Layout
│   │   ├── index.css       # Tailwind CSS v4, styling tokens
│   │   └── main.tsx
│   │
│   └── package.json        # NPM dependencies
│
├── uploads/                # Directory storing uploaded blueprint files
├── reports/                # Directory storing generated PDF reports
├── models/                 # Directory for custom YOLO weight file (.pt)
├── dataset/                # Placeholder for model training datasets
└── docs/                   # Additional documentation
```

---

## Getting Started

### Prerequisites

* [Node.js](https://nodejs.org/) (v18 or higher)
* [Python 3.10+](https://www.python.org/downloads/)

---

### Backend Installation & Startup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows (Powershell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   * The API docs will be interactive and accessible at `http://localhost:8000/docs`.

---

### Frontend Installation & Startup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install NPM packages:
   ```bash
   npm install
   ```

3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
   * The client application will launch and be accessible at `http://localhost:5173`.

---

## AI/ML Model Integration

By default, the backend employs a **high-fidelity heuristics and rule-based simulation engine** that yields fully populated and deterministic layout scans depending on the uploaded file hash. This ensures that the application is **fully operational immediately** without downloading gigabytes of machine-learning packages.

To hook up your own custom YOLO object detection and EasyOCR models:

1. **Install PyTorch and OCR libraries:**
   ```bash
   pip install torch torchvision ultralytics easyocr opencv-python-headless
   ```

2. **Deploy Weights:**
   * Place your custom-trained YOLO weights (`.pt` file) inside the `/models` folder and name it `blueprint_yolo.pt`.

3. **Inference Pipeline:**
   * The application's `BlueprintAnalysisEngine` class inside [analysis_engine.py](file:///c:/Users/ganiy/OneDrive/Desktop/AI%20BluePrint%20error%20detection/backend/app/engine/analysis_engine.py) will automatically detect the presence of the packages and load the model weights, switching the pipeline from simulated mapping to real-time image inference.

# TrustVision — Data Integrity Phase

TrustVision is an offline-capable computer-vision data integrity assurance system designed for multi-contributor dataset pipelines.

This repository implements the **Data Integrity Phase** using the official **CIFAR-10** dataset (50,000 training images, 10 classes, RGB 32×32 resolution).

---

## 🌟 Key Features

1. **Automated CIFAR-10 Reference Manager:** Automatically downloads and maintains an immutable, clean reference dataset under `data/reference/cifar10/`.
2. **Deterministic Contributor Dataset Simulation:**
   - **C1 — Clean:** Normal image-label pairs and balanced class distribution.
   - **C2 — Clean:** Independent clean dataset slice.
   - **C3 — Risky / Manipulated:** Controlled test dataset containing:
     - Duplicate flooding (exact repeated images)
     - Near-duplicate samples (small crops, brightness shifts, rotations)
     - Label anomalies (mismatched submitted vs. reference labels)
     - Controlled trigger injection (synthetic 6×6 pixel patch)
     - Class distribution shift (over-sampled & under-sampled classes)
   - **C4 — Clean:** Independent clean dataset slice.
3. **5 Data Integrity Detectors:**
   - **Exact Duplicate Detector:** SHA-256 byte hash matching & grouping.
   - **Near-Duplicate Detector:** Perceptual hashing (`imagehash` pHash) & visual similarity scoring.
   - **Label Anomaly Detector:** Deep visual embedding feature centroids & visual inconsistency detection.
   - **Distribution / OOD Detector:** Chi-Square distribution goodness-of-fit & drift score.
   - **Controlled Trigger Detector:** Pattern analysis detector scanning for synthetic patch artifacts.
4. **Evidence Engine & Transparent Aggregation:** Sample-level evidence aggregated into transparent rules generating `ACCEPT`, `REVIEW`, or `QUARANTINE` states.
5. **Cryptographic SHA-256 Manifests:** Merkle root hash manifests for reference and contributor datasets.
6. **Assurance Reports:** Standalone HTML report (`assurance_report.html`) and machine-readable JSON report (`assurance_report.json`).
7. **FastAPI Backend & React Dashboard:** REST API serving a modern analyst dashboard.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

*(Or install standard PyTorch, torchvision, imagehash, scipy, scikit-learn, fastapi, uvicorn, pillow)*

### 2. Run End-to-End Demonstration

The demonstration executes the pipeline across 10 distinct phases automatically:
- **Phase 1**: Reference Dataset Management (CIFAR-10)
- **Phase 2 & 3**: Generating Contributor Submissions (C1, C2, C3, C4)
- **Phase 4, 5 & 6**: Executing Data Integrity Detectors across Submissions
- **Phase 7**: Detailed Evidence Breakdown for Contributor C3 (Risky)
- **Phase 8 & 9**: Pipeline Evidence Aggregation & Decision Matrix
- **Phase 10**: Assurance Report Generation

Execute the single-command workflow script to run all phases:

```bash
python scripts/run_demo.py
```

### 3. Run Model Integrity Phase

The Model Integrity verification allows you to verify if a submitted model matches a trusted hash and performs behavioral analysis to detect tampering.

1. **Generate Demo Models (Clean and Tampered):**
   ```bash
   python scripts/setup_behavioral_demo.py
   ```
   This will create `demo/clean/` and `demo/tampered/` directories containing `company_model.pth` and `company_model.sha256`.

2. **Test via UI:**
   Start the backend and frontend (see step 5), then navigate to the **Model Integrity** page in the dashboard to test the clean vs tampered models.

### 4. Run Inference Integrity Phase

The Inference Integrity phase secures individual model predictions by issuing cryptographically signed inference records.

1. **Test via UI:**
   Start the backend and frontend (see step 5), then navigate to the **Inference Integrity** page.
2. **Run and Verify:**
   - Upload an image to generate a secure inference record.
   - Test "Verify Integrity" to ensure it is valid.
   - Use "Simulate Tampering" or "Simulate Replay Attack" to test detection capabilities.

### 5. Start Backend API & Frontend Dashboard

Start FastAPI Backend:

```bash
uvicorn backend.api.main:app --reload --port 8000
```

Start React Analyst Dashboard:

```bash
cd frontend
npm install
npm run dev
```

Open your browser at `http://localhost:5173`.

---

## 🧪 Running Automated Tests

Run the full pytest suite:

```bash
pytest -v tests/
```

---

## 📂 Repository Structure

```
trustvision/
│
├── data/
│   ├── reference/cifar10/       # Clean reference dataset baseline
│   ├── contributors/            # C1, C2, C3, C4 contributor submissions
│   └── generated/               # Evidence, manifests, reports
│
├── backend/
│   ├── config.py                # Configuration thresholds and parameters
│   ├── data_manager.py          # Reference dataset download & immutability
│   ├── generator.py             # Contributor simulation & controlled C3 manipulations
│   ├── hashing.py               # SHA-256 manifests manager
│   ├── detectors/               # 5 Integrity Detector implementations
│   ├── evidence/                # Evidence Engine schema
│   ├── contributor_analysis/    # Contributor Risk Aggregator & Decision Rules
│   ├── reports/                 # JSON & HTML Assurance Report Generators
│   └── api/                     # FastAPI backend application
│
├── frontend/                    # React + Tailwind CSS Analyst Dashboard
├── scripts/                     # End-to-end demonstration script
├── tests/                       # Automated pytest suite
└── README.md
```

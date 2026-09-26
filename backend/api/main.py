import json
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging

from backend.config import (
    BASE_DIR, DATA_DIR, CONTRIBUTORS_DIR, REPORTS_DIR, EVIDENCE_DIR, MANIFESTS_DIR
)
from backend.data_manager import ReferenceDataManager
from backend.generator import ContributorGenerator
from backend.hashing import ManifestManager
from backend.evidence.engine import EvidenceEngine
from backend.contributor_analysis.aggregator import ContributorAggregator
from backend.reports.generator import ReportGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustVision.API")

app = FastAPI(
    title="TrustVision API",
    description="Offline-capable Data Integrity Assurance API for Computer Vision Pipelines",
    version="1.0.0"
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static image data route
if DATA_DIR.exists():
    app.mount("/static/data", StaticFiles(directory=str(DATA_DIR)), name="static_data")

# Core services initialization
data_mgr = ReferenceDataManager()
generator = ContributorGenerator()
manifest_mgr = ManifestManager()
evidence_engine = EvidenceEngine()
aggregator = ContributorAggregator()
report_gen = ReportGenerator()


@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "TrustVision Data Integrity Assurance Engine",
        "version": "1.0.0"
    }


@app.post("/datasets/download")
def download_cifar10(force: bool = False):
    """
    Downloads and prepares official CIFAR-10 reference dataset.
    """
    try:
        manifest = data_mgr.download_and_extract(force=force)
        return {
            "status": "success",
            "message": f"CIFAR-10 reference dataset ready with {len(manifest['samples'])} samples.",
            "total_samples": len(manifest['samples'])
        }
    except Exception as e:
        logger.error(f"Error downloading CIFAR-10: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contributors/generate")
def generate_contributors(seed: int = 42, samples_per_contributor: int = 2000):
    """
    Generates C1, C2, C3 (risky), C4 simulated contributor datasets.
    """
    try:
        generator.seed = seed
        generator.samples_per_contributor = samples_per_contributor
        results = generator.generate_all()

        # Generate cryptographic manifests for each contributor
        crypto_manifests = {}
        for cid in ["C1", "C2", "C3", "C4"]:
            contrib_dirs = list(CONTRIBUTORS_DIR.glob(f"{cid}_*"))
            if contrib_dirs:
                m = manifest_mgr.create_contributor_manifest(cid, contrib_dirs[0])
                crypto_manifests[cid] = m["dataset_root_hash"]

        return {
            "status": "success",
            "message": "Generated simulated contributors C1, C2, C3, C4 successfully.",
            "contributors": results,
            "crypto_root_hashes": crypto_manifests
        }
    except Exception as e:
        logger.error(f"Error generating contributors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/contributors/upload")
async def upload_contributor(
    contributor_id: str = Form(...),
    description: str = Form("Manual upload"),
    file: UploadFile = File(...)
):
    """
    Manually upload a ZIP file or image file containing contributor data.
    Handles BadZipFile central directory offsets and direct image uploads safely.
    """
    try:
        import zipfile
        import shutil

        contrib_dir = CONTRIBUTORS_DIR / contributor_id
        if contrib_dir.exists():
            shutil.rmtree(contrib_dir)
        contrib_dir.mkdir(parents=True, exist_ok=True)

        zip_path = contrib_dir / file.filename
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted = False

        # Strategy 1: Standard zipfile extraction
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(contrib_dir)
            extracted = True
        except (zipfile.BadZipFile, Exception) as ze:
            logger.warning(f"Standard zipfile extraction failed for {file.filename}: {ze}. Attempting fallback unpack...")
            # Strategy 2: shutil.unpack_archive fallback
            try:
                shutil.unpack_archive(str(zip_path), str(contrib_dir))
                extracted = True
            except Exception as unpack_err:
                logger.warning(f"shutil.unpack_archive failed: {unpack_err}")

        # If not a zip archive, check if a single direct image file was uploaded
        if not extracted:
            ext = Path(file.filename).suffix.lower()
            if ext in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                images_dir = contrib_dir / "images"
                images_dir.mkdir(parents=True, exist_ok=True)
                dest_img = images_dir / file.filename
                shutil.move(str(zip_path), str(dest_img))
                extracted = True
            else:
                if zip_path.exists():
                    zip_path.unlink()
                raise HTTPException(
                    status_code=400,
                    detail=f"Uploaded file '{file.filename}' is corrupt or not a valid ZIP archive (Bad offset for central directory). Please ensure it is a valid .zip file."
                )

        if zip_path.exists():
            zip_path.unlink()

        # Handle nested folder if zip contains a single top-level folder
        items = [i for i in contrib_dir.iterdir() if i.is_dir()]
        if len(items) == 1 and items[0].name != "images":
            inner_dir = items[0]
            for item in inner_dir.iterdir():
                shutil.move(str(item), str(contrib_dir))
            inner_dir.rmdir()

        m = manifest_mgr.create_contributor_manifest(contributor_id, contrib_dir)

        meta = {
            "contributor_id": contributor_id,
            "dataset_name": f"Manual_{contributor_id}",
            "type": "MANUAL",
            "description": description,
            "sample_count": m.get("total_samples", len(list(contrib_dir.rglob("*.png"))))
        }
        with open(contrib_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return {
            "status": "success",
            "message": f"Contributor {contributor_id} uploaded successfully with {meta['sample_count']} samples.",
            "contributor_id": contributor_id,
            "sample_count": meta['sample_count'],
            "crypto_root_hash": m.get("dataset_root_hash")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading contributor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/contributors/{contributor_id}")
def delete_contributor(contributor_id: str):
    import shutil
    contrib_dir = CONTRIBUTORS_DIR / contributor_id
    if contrib_dir.exists():
        shutil.rmtree(contrib_dir)
        return {"status": "success", "message": f"Deleted {contributor_id}"}
    raise HTTPException(status_code=404, detail="Contributor not found")


@app.get("/contributors")
def list_contributors():
    """
    Lists generated contributor datasets and their metadata.
    """
    contributors_list = []
    for contrib_dir in sorted(CONTRIBUTORS_DIR.iterdir()):
        if contrib_dir.is_dir():
            meta_file = contrib_dir / "metadata.json"
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                contributors_list.append(metadata)
    return {"contributors": contributors_list}


@app.post("/analyze/{contributor_id}")
def analyze_contributor(contributor_id: str):
    """
    Executes 5 integrity detectors and evaluates risk decision for a single contributor.
    """
    try:
        evidence_pkg = evidence_engine.analyze_contributor(contributor_id)
        evaluation = aggregator.evaluate(evidence_pkg)

        # Save evaluation result
        res_file = EVIDENCE_DIR / f"{contributor_id}_evaluation.json"
        with open(res_file, "w", encoding="utf-8") as f:
            json.dump(evaluation, f, indent=2)

        return {
            "status": "success",
            "contributor_id": contributor_id,
            "decision": evaluation["decision"],
            "risk_score": evaluation["risk_score"],
            "evaluation": evaluation,
            "evidence_events_count": evidence_pkg["total_evidence_events"]
        }
    except Exception as e:
        logger.error(f"Error analyzing {contributor_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/all")
def analyze_all():
    """
    Executes integrity detectors for all contributors and generates JSON/HTML assurance reports.
    """
    try:
        evaluations = []
        contributors = [d.name for d in CONTRIBUTORS_DIR.iterdir() if d.is_dir()]
        for cid in contributors:
            evidence_pkg = evidence_engine.analyze_contributor(cid)
            eval_res = aggregator.evaluate(evidence_pkg)
            evaluations.append(eval_res)

        # Generate reports
        crypto_manifests = {}
        for cid in contributors:
            mf_path = MANIFESTS_DIR / f"{cid}_manifest.json"
            if mf_path.exists():
                with open(mf_path, "r", encoding="utf-8") as f:
                    crypto_manifests[cid] = json.load(f).get("dataset_root_hash", "")

        json_path = report_gen.generate_json_report(
            project_name="TrustVision",
            dataset_name="CIFAR-10",
            contributor_evaluations=evaluations,
            crypto_manifests=crypto_manifests
        )

        html_path = report_gen.generate_html_report(json_path)

        return {
            "status": "success",
            "message": "Analyzed all contributors and generated assurance reports.",
            "evaluations": evaluations,
            "json_report": str(json_path.name),
            "html_report": str(html_path.name)
        }
    except Exception as e:
        logger.error(f"Error analyzing all contributors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/{contributor_id}")
def get_results(contributor_id: str):
    """
    Gets evaluation result and evidence breakdown for a contributor.
    """
    res_file = EVIDENCE_DIR / f"{contributor_id}_evaluation.json"
    ev_file = EVIDENCE_DIR / f"{contributor_id}_evidence.json"

    if not res_file.exists() or not ev_file.exists():
        analyze_contributor(contributor_id)

    with open(res_file, "r", encoding="utf-8") as f:
        evaluation = json.load(f)

    # Automatically re-analyze if evaluation contains a stale uncapped score > 100
    if evaluation.get("risk_score", 0) > 100.0:
        analyze_contributor(contributor_id)
        with open(res_file, "r", encoding="utf-8") as f:
            evaluation = json.load(f)

    with open(ev_file, "r", encoding="utf-8") as f:
        evidence = json.load(f)

    return {
        "evaluation": evaluation,
        "evidence": evidence
    }


@app.get("/reports/{contributor_id}")
def get_report(contributor_id: str):
    """
    Returns full JSON assurance report.
    """
    json_path = REPORTS_DIR / "assurance_report.json"
    if not json_path.exists():
        analyze_all()

    with open(json_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Check if any contributor in report has stale risk score > 100
    has_stale = any(c.get("risk_score", 0) > 100.0 for c in report.get("contributors", []))
    if has_stale:
        analyze_all()
        with open(json_path, "r", encoding="utf-8") as f:
            report = json.load(f)

    return report


@app.get("/reports/view/html", response_class=HTMLResponse)
def get_html_report():
    """
    Serves formatted HTML assurance report directly in browser.
    """
    html_path = REPORTS_DIR / "assurance_report.html"
    if not html_path.exists():
        analyze_all()

    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

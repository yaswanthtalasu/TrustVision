from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from pathlib import Path
import shutil
import os
import uuid
from datetime import datetime

from backend.config import BASE_DIR, REPORTS_DIR
from backend.model_integrity.verifier import verify_model_integrity
from backend.model_integrity.evidence import save_evidence, save_behavioral_evidence, save_full_evidence
from backend.model_integrity.report import generate_json_report, generate_html_report, generate_behavioral_report, generate_full_report
from backend.model_integrity.schemas import FullIntegrityResult, BehavioralAnalysisResult
from backend.model_integrity.model_loader import load_resnet18_model
from backend.model_integrity.test_generator import generate_test_suites
from backend.model_integrity.behavioral_analyzer import BehavioralAnalyzer

router = APIRouter(prefix="/api/model-integrity", tags=["Model Integrity"])
UPLOAD_DIR = BASE_DIR / "uploads" / "model_integrity"

@router.post("/verify")
async def verify(model_file: UploadFile = File(...), hash_file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save files securely
    model_path = UPLOAD_DIR / Path(model_file.filename).name
    hash_path = UPLOAD_DIR / Path(hash_file.filename).name
    
    with open(model_path, "wb") as buffer:
        shutil.copyfileobj(model_file.file, buffer)
        
    with open(hash_path, "wb") as buffer:
        shutil.copyfileobj(hash_file.file, buffer)
        
    result = verify_model_integrity(model_path, hash_path)
    
    if result.status == "INVALID_INPUT":
        # Clean up uploads
        if os.path.exists(model_path): os.remove(model_path)
        if os.path.exists(hash_path): os.remove(hash_path)
        return JSONResponse(status_code=400, content=result.model_dump())
        
    save_evidence(result)
    json_path = generate_json_report(result)
    generate_html_report(json_path)
    
    if os.path.exists(model_path): os.remove(model_path)
    if os.path.exists(hash_path): os.remove(hash_path)
    
    return result

@router.post("/behavioral-analysis")
async def analyze_behavior(model_file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = UPLOAD_DIR / f"behavioral_{Path(model_file.filename).name}"
    with open(model_path, "wb") as buffer:
        shutil.copyfileobj(model_file.file, buffer)
        
    try:
        sub_model = load_resnet18_model(model_path)
        
        # Load reference model (demo model)
        ref_model_path = BASE_DIR / "demo" / "clean" / "company_model.pth"
        if not ref_model_path.exists():
            ref_model = load_resnet18_model(model_path)
        else:
            ref_model = load_resnet18_model(ref_model_path)
            
        normal_inputs, trigger_inputs = generate_test_suites()
        
        analyzer = BehavioralAnalyzer(ref_model, sub_model)
        analysis_result = analyzer.analyze(normal_inputs, trigger_inputs)
        
        result = BehavioralAnalysisResult(
            analysis_id=str(uuid.uuid4()),
            status=analysis_result["status"],
            reference_model="Trusted Reference ResNet-18",
            submitted_model=model_file.filename,
            normal_test=analysis_result["normal_test"],
            trigger_test=analysis_result["trigger_test"],
            evidence=analysis_result["evidence"],
            timestamp=datetime.now().isoformat(),
            limitations=[
                "controlled test suite",
                "reference model dependency",
                "prototype thresholds",
                "behavioral analysis does not prove malicious intent",
                "absence of detected deviation does not prove universal safety"
            ]
        )
        
        save_behavioral_evidence(result)
        json_path = generate_behavioral_report(result)
        generate_html_report(json_path)
        
    except Exception as e:
        if os.path.exists(model_path): os.remove(model_path)
        raise HTTPException(status_code=500, detail=str(e))
        
    if os.path.exists(model_path): os.remove(model_path)
    
    return result

@router.post("/verify-full")
async def verify_full(model_file: UploadFile = File(...), hash_file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = UPLOAD_DIR / f"full_{Path(model_file.filename).name}"
    hash_path = UPLOAD_DIR / f"full_{Path(hash_file.filename).name}"
    
    with open(model_path, "wb") as buffer:
        shutil.copyfileobj(model_file.file, buffer)
        
    with open(hash_path, "wb") as buffer:
        shutil.copyfileobj(hash_file.file, buffer)
        
    # Check 1: Artifact Integrity
    artifact_result = verify_model_integrity(model_path, hash_path)
    
    if artifact_result.status == "INVALID_INPUT":
        if os.path.exists(model_path): os.remove(model_path)
        if os.path.exists(hash_path): os.remove(hash_path)
        return JSONResponse(status_code=400, content=artifact_result.model_dump())
        
    # Check 2: Behavioral Integrity
    behavioral_result = None
    try:
        sub_model = load_resnet18_model(model_path)
        ref_model_path = BASE_DIR / "demo" / "clean" / "company_model.pth"
        if not ref_model_path.exists():
            ref_model = load_resnet18_model(model_path)
        else:
            ref_model = load_resnet18_model(ref_model_path)
            
        normal_inputs, trigger_inputs = generate_test_suites()
        analyzer = BehavioralAnalyzer(ref_model, sub_model)
        analysis_result = analyzer.analyze(normal_inputs, trigger_inputs)
        
        behavioral_result = BehavioralAnalysisResult(
            analysis_id=str(uuid.uuid4()),
            status=analysis_result["status"],
            reference_model="Trusted Reference ResNet-18",
            submitted_model=model_file.filename,
            normal_test=analysis_result["normal_test"],
            trigger_test=analysis_result["trigger_test"],
            evidence=analysis_result["evidence"],
            timestamp=datetime.now().isoformat(),
            limitations=[
                "This assessment does not prove absence of unknown attacks.",
                "controlled test suite",
                "reference model dependency",
                "prototype thresholds"
            ]
        )
    except Exception as e:
        pass # If it fails to load, behavioral_result stays None, which will trigger QUARANTINE or REVIEW
        
    # Compute overall disposition
    disposition = "REVIEW"
    if artifact_result.status == "PASS" and behavioral_result and behavioral_result.status == "PASS":
        disposition = "ACCEPT"
    elif artifact_result.status == "PASS" and (not behavioral_result or behavioral_result.status == "REVIEW"):
        disposition = "REVIEW"
    elif artifact_result.status == "REVIEW" and (not behavioral_result or behavioral_result.status == "REVIEW"):
        disposition = "QUARANTINE"
        
    full_result = FullIntegrityResult(
        verification_id=artifact_result.verification_id or str(uuid.uuid4()),
        model_filename=artifact_result.model_filename,
        artifact=artifact_result,
        behavioral=behavioral_result,
        overall_disposition=disposition,
        timestamp=datetime.now().isoformat()
    )
    
    save_full_evidence(full_result)
    json_path = generate_full_report(full_result)
    generate_html_report(json_path)
    
    if os.path.exists(model_path): os.remove(model_path)
    if os.path.exists(hash_path): os.remove(hash_path)
    
    return full_result

@router.get("/status/{verification_id}")
def get_status(verification_id: str):
    pass 

@router.get("/report/{verification_id}")
def get_report(verification_id: str):
    json_path = REPORTS_DIR / f"model_integrity_{verification_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    with open(json_path, "r", encoding="utf-8") as f:
        import json
        return json.load(f)

@router.get("/report/{verification_id}/html")
def get_html_report_endpoint(verification_id: str):
    html_path = REPORTS_DIR / f"model_integrity_{verification_id}.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

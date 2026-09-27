import json
from pathlib import Path
from backend.config import EVIDENCE_DIR
from backend.model_integrity.schemas import VerificationResult

def save_evidence(result: VerificationResult):
    if not result.verification_id:
        return
        
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_path = EVIDENCE_DIR / f"model_integrity_{result.verification_id}.json"
    
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

def save_behavioral_evidence(result):
    if not result.analysis_id:
        return
        
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    evidence_path = EVIDENCE_DIR / f"behavioral_integrity_{result.analysis_id}.json"
    
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)


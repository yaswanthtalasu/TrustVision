from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VerificationResult(BaseModel):
    verification_id: Optional[str] = None
    model_filename: str
    hash_algorithm: str = "SHA-256"
    claimed_hash: Optional[str] = None
    computed_hash: Optional[str] = None
    match: bool = False
    status: str
    verification_timestamp: str
    file_size_bytes: int

class BehavioralAnalysisResult(BaseModel):
    analysis_id: str
    status: str
    reference_model: str
    submitted_model: str
    normal_test: dict
    trigger_test: dict
    evidence: list
    timestamp: str
    limitations: list

class FullIntegrityResult(BaseModel):
    verification_id: str
    model_filename: str
    artifact: VerificationResult
    behavioral: Optional[BehavioralAnalysisResult] = None
    overall_disposition: str
    timestamp: str


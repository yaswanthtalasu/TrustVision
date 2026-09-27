from pydantic import BaseModel
from typing import Optional, Dict, Any

class InferenceRecord(BaseModel):
    record_id: str
    sequence_id: int
    timestamp: str
    input_hash: str
    model_hash: str
    model_id: str
    preprocessing_config: str
    prediction: str
    confidence: float
    previous_record_hash: Optional[str] = None
    record_hash: Optional[str] = None
    signature: Optional[str] = None
    key_id: Optional[str] = None

class VerificationResult(BaseModel):
    status: str
    record_id: str
    checks: Dict[str, str]
    evidence: list[str]

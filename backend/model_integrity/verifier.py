import uuid
from pathlib import Path
from datetime import datetime
from backend.model_integrity.hash_utils import calculate_sha256, parse_sha256_file
from backend.model_integrity.schemas import VerificationResult

def verify_model_integrity(model_path: Path, hash_path: Path) -> VerificationResult:
    timestamp = datetime.now().isoformat()
    file_size = model_path.stat().st_size if model_path.exists() else 0
    filename = model_path.name
    
    if not model_path.exists() or not hash_path.exists():
        return VerificationResult(
            verification_id=None,
            model_filename=filename,
            status="INVALID_INPUT",
            verification_timestamp=timestamp,
            file_size_bytes=file_size
        )
        
    claimed_hash = parse_sha256_file(hash_path)
    if not claimed_hash:
        return VerificationResult(
            verification_id=None,
            model_filename=filename,
            status="INVALID_INPUT",
            verification_timestamp=timestamp,
            file_size_bytes=file_size
        )
        
    computed_hash = calculate_sha256(model_path)
    match = (claimed_hash == computed_hash)
    status = "PASS" if match else "REVIEW"
    
    return VerificationResult(
        verification_id=str(uuid.uuid4()),
        model_filename=filename,
        claimed_hash=claimed_hash,
        computed_hash=computed_hash,
        match=match,
        status=status,
        verification_timestamp=timestamp,
        file_size_bytes=file_size
    )

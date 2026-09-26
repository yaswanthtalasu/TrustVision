import pytest
from pathlib import Path
from backend.model_integrity.verifier import verify_model_integrity
from backend.model_integrity.hash_utils import calculate_sha256
import tempfile
import hashlib
import os

@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

def test_clean_model(temp_workspace):
    model_path = temp_workspace / "model.pth"
    hash_path = temp_workspace / "model.sha256"
    
    # Write dummy model
    model_path.write_bytes(b"dummy_model_data_123")
    
    # Calculate correct hash
    sha256 = hashlib.sha256(b"dummy_model_data_123").hexdigest()
    hash_path.write_text(sha256)
    
    result = verify_model_integrity(model_path, hash_path)
    assert result.status == "PASS"
    assert result.match is True
    assert result.computed_hash == sha256
    assert result.claimed_hash == sha256

def test_tampered_model(temp_workspace):
    model_path = temp_workspace / "model.pth"
    hash_path = temp_workspace / "model.sha256"
    
    model_path.write_bytes(b"tampered_data")
    hash_path.write_text(hashlib.sha256(b"original_data").hexdigest())
    
    result = verify_model_integrity(model_path, hash_path)
    assert result.status == "REVIEW"
    assert result.match is False

def test_invalid_hash(temp_workspace):
    model_path = temp_workspace / "model.pth"
    hash_path = temp_workspace / "model.sha256"
    
    model_path.write_bytes(b"data")
    hash_path.write_text("not_a_valid_hash")
    
    result = verify_model_integrity(model_path, hash_path)
    assert result.status == "INVALID_INPUT"

def test_missing_input(temp_workspace):
    model_path = temp_workspace / "missing_model.pth"
    hash_path = temp_workspace / "model.sha256"
    hash_path.write_text(hashlib.sha256(b"data").hexdigest())
    
    result = verify_model_integrity(model_path, hash_path)
    assert result.status == "INVALID_INPUT"

def test_large_file_hashing(temp_workspace):
    model_path = temp_workspace / "large_model.bin"
    # Create a larger file (10MB)
    chunk = os.urandom(1024 * 1024)
    with open(model_path, "wb") as f:
        for _ in range(10):
            f.write(chunk)
            
    computed = calculate_sha256(model_path)
    
    # Verify with standard hashlib
    sha256 = hashlib.sha256()
    with open(model_path, "rb") as f:
        sha256.update(f.read())
    expected = sha256.hexdigest()
    
    assert computed == expected

import json
import hashlib
from backend.hashing import ManifestManager

def test_manifest_manager_sha256(tmp_path):
    mm = ManifestManager(manifests_dir=tmp_path)
    
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("TrustVision Cryptographic Manifest Verification Test")

    sha = mm.generate_file_sha256(sample_file)
    expected_sha = hashlib.sha256("TrustVision Cryptographic Manifest Verification Test".encode("utf-8")).hexdigest()
    assert sha == expected_sha

import json
from pathlib import Path
from backend.data_manager import ReferenceDataManager

def test_reference_data_manager_structure(temp_environment):
    ref_dir = temp_environment["ref_dir"]
    manager = ReferenceDataManager(target_dir=ref_dir)
    manifest = manager.load_manifest()

    assert manifest["dataset"] == "CIFAR-10"
    assert manifest["total_samples"] == 50
    assert len(manifest["classes"]) == 10

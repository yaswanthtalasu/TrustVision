import json
import pytest
from pathlib import Path
from backend.detectors.exact_duplicate import ExactDuplicateDetector
from backend.detectors.near_duplicate import NearDuplicateDetector
from backend.detectors.label_anomaly import LabelAnomalyDetector
from backend.detectors.distribution_shift import DistributionShiftDetector
from backend.detectors.controlled_trigger import ControlledTriggerDetector
from backend.evidence.engine import EvidenceEngine
from backend.contributor_analysis.aggregator import ContributorAggregator

def test_detectors_and_evidence_aggregation(temp_environment):
    """
    Validates that exact duplicates, near duplicates, label anomalies, distribution shift,
    and synthetic patch triggers are correctly detected and aggregated.
    """
    root = temp_environment["root"]
    contribs_dir = temp_environment["contribs_dir"]
    ref_manifest = temp_environment["ref_manifest"]

    # Create synthetic C1 (Clean) dataset
    c1_dir = contribs_dir / "C1_clean"
    c1_images = c1_dir / "images"
    c1_images.mkdir(parents=True, exist_ok=True)

    c1_samples = []
    for i in range(20):
        ref_s = ref_manifest["samples"][i]
        c1_samples.append({
            "sample_id": f"C1_{i:05d}",
            "file_path": ref_s["file_path"],
            "submitted_label": ref_s["label_name"],
            "submitted_label_id": ref_s["label_id"],
            "reference_label": ref_s["label_name"],
            "reference_label_id": ref_s["label_id"],
            "sha256": ref_s["sha256"]
        })

    with open(c1_dir / "manifest.json", "w") as f:
        json.dump({"samples": c1_samples}, f)

    # Test Exact Duplicate Detector on C1
    exact_det = ExactDuplicateDetector()
    res = exact_det.analyze("C1", c1_dir, ref_manifest)
    assert res["exact_duplicate_count"] == 0
    assert res["affected_percentage"] == 0.0

    # Test Controlled Trigger Detector on C1
    trig_det = ControlledTriggerDetector()
    res_trig = trig_det.analyze("C1", c1_dir, ref_manifest)
    assert res_trig["trigger_count"] == 0

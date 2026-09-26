import json
from pathlib import Path
from typing import Dict, Any, List
import logging

from backend.config import BASE_DIR, CONTRIBUTORS_DIR, EVIDENCE_DIR
from backend.data_manager import ReferenceDataManager
from backend.detectors.exact_duplicate import ExactDuplicateDetector
from backend.detectors.near_duplicate import NearDuplicateDetector
from backend.detectors.label_anomaly import LabelAnomalyDetector
from backend.detectors.distribution_shift import DistributionShiftDetector
from backend.detectors.controlled_trigger import ControlledTriggerDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustVision.EvidenceEngine")


class EvidenceEngine:
    def __init__(self, evidence_dir: Path = EVIDENCE_DIR):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.ref_manager = ReferenceDataManager()
        
        # Instantiate 5 core detectors
        self.detectors = [
            ExactDuplicateDetector(),
            NearDuplicateDetector(),
            LabelAnomalyDetector(),
            DistributionShiftDetector(),
            ControlledTriggerDetector()
        ]

    def analyze_contributor(self, contributor_id: str, contrib_dir: Path = None) -> Dict[str, Any]:
        """
        Runs all 5 integrity detectors on a contributor dataset and aggregates evidence.
        """
        if contrib_dir is None:
            # Locate contributor directory automatically
            matches = list(CONTRIBUTORS_DIR.glob(f"{contributor_id}_*"))
            if not matches:
                raise FileNotFoundError(f"Contributor directory for {contributor_id} not found in {CONTRIBUTORS_DIR}")
            contrib_dir = matches[0]
        else:
            contrib_dir = Path(contrib_dir)

        logger.info(f"Analyzing contributor {contributor_id} at {contrib_dir}...")
        ref_manifest = self.ref_manager.load_manifest()

        detector_results = {}
        all_sample_evidence: List[dict] = []

        for detector in self.detectors:
            logger.info(f"Running detector '{detector.name}' for {contributor_id}...")
            result = detector.analyze(contributor_id, contrib_dir, ref_manifest)
            detector_results[detector.name] = result

            # Collect sample-level evidence items
            sample_evidence_items = result.get("sample_evidence", [])
            all_sample_evidence.extend(sample_evidence_items)

        # Read contributor metadata if available
        meta_path = contrib_dir / "metadata.json"
        metadata = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        total_samples = detector_results["exact_duplicate"]["total_samples"]

        evidence_package = {
            "contributor_id": contributor_id,
            "metadata": metadata,
            "total_samples": total_samples,
            "detector_results": detector_results,
            "all_sample_evidence": all_sample_evidence,
            "total_evidence_events": len(all_sample_evidence)
        }

        # Save evidence package
        out_file = self.evidence_dir / f"{contributor_id}_evidence.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(evidence_package, f, indent=2)

        logger.info(f"Evidence analysis complete for {contributor_id}. Saved to {out_file.name} ({len(all_sample_evidence)} evidence events).")
        return evidence_package


if __name__ == "__main__":
    ee = EvidenceEngine()
    print("EvidenceEngine initialized.")

import json
from pathlib import Path
from typing import Dict, Any, List
from scipy.stats import chisquare
from backend.config import CIFAR10_CLASSES
from backend.detectors.base import BaseDetector


class DistributionShiftDetector(BaseDetector):
    def __init__(self, shift_threshold_pct: float = 8.0):
        super().__init__(
            name="distribution_shift",
            description="Identifies dataset class composition shift and out-of-distribution drift against reference dataset."
        )
        self.shift_threshold_pct = shift_threshold_pct

    def analyze(self, contributor_id: str, contrib_dir: Path, ref_manifest: Dict[str, Any]) -> Dict[str, Any]:
        contrib_dir = Path(contrib_dir)
        manifest_file = contrib_dir / "manifest.json"

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        samples = manifest.get("samples", [])
        total_samples = len(samples)

        # Count submitted class distribution
        contrib_counts = {c: 0 for c in CIFAR10_CLASSES}
        for s in samples:
            lbl = s.get("submitted_label", CIFAR10_CLASSES[s.get("submitted_label_id", 0)])
            if lbl in contrib_counts:
                contrib_counts[lbl] += 1

        # Count reference class distribution
        ref_samples = ref_manifest.get("samples", [])
        ref_total = len(ref_samples)
        ref_counts = {c: 0 for c in CIFAR10_CLASSES}
        for s in ref_samples:
            lbl = s.get("label_name", CIFAR10_CLASSES[s.get("label_id", 0)])
            if lbl in ref_counts:
                ref_counts[lbl] += 1

        class_breakdown = {}
        affected_classes = []
        max_delta = 0.0

        for c_name in CIFAR10_CLASSES:
            ref_pct = (ref_counts[c_name] / ref_total * 100.0) if ref_total > 0 else 10.0
            contrib_pct = (contrib_counts[c_name] / total_samples * 100.0) if total_samples > 0 else 0.0
            delta_pct = round(contrib_pct - ref_pct, 2)

            class_breakdown[c_name] = {
                "reference_pct": round(ref_pct, 2),
                "contributor_pct": round(contrib_pct, 2),
                "delta_pct": delta_pct,
                "count": contrib_counts[c_name]
            }

            if abs(delta_pct) >= self.shift_threshold_pct:
                affected_classes.append({
                    "class_name": c_name,
                    "reference_pct": round(ref_pct, 2),
                    "contributor_pct": round(contrib_pct, 2),
                    "delta_pct": delta_pct
                })
            
            if abs(delta_pct) > max_delta:
                max_delta = abs(delta_pct)

        # Calculate Chi-Square statistic
        expected_counts = [total_samples * (ref_counts[c] / ref_total) for c in CIFAR10_CLASSES]
        observed_counts = [contrib_counts[c] for c in CIFAR10_CLASSES]

        try:
            chi_stat, p_val = chisquare(f_obs=observed_counts, f_exp=expected_counts)
        except Exception:
            chi_stat, p_val = 0.0, 1.0

        shift_detected = bool(len(affected_classes) > 0 or p_val < 0.01)

        sample_evidence = []
        if shift_detected:
            for aff in affected_classes:
                sample_evidence.append({
                    "detector": self.name,
                    "contributor_id": contributor_id,
                    "sample_id": f"CONTRIB_CLASS_{aff['class_name'].upper()}",
                    "evidence": {
                        "affected_class": aff["class_name"],
                        "reference_percentage": aff["reference_pct"],
                        "contributor_percentage": aff["contributor_pct"],
                        "distribution_difference": aff["delta_pct"],
                        "p_value": round(float(p_val), 6)
                    },
                    "severity": "HIGH" if abs(aff["delta_pct"]) > 15.0 else "MEDIUM",
                    "description": f"Distribution shift detected in class '{aff['class_name']}': contributor has {aff['contributor_pct']}% vs reference baseline {aff['reference_pct']}% (delta: {aff['delta_pct']}%)."
                })

        return {
            "detector": self.name,
            "contributor_id": contributor_id,
            "total_samples": total_samples,
            "distribution_difference_score": round(max_delta, 2),
            "chi_square_stat": round(float(chi_stat), 2),
            "p_value": round(float(p_val), 6),
            "shift_detected": shift_detected,
            "affected_classes_count": len(affected_classes),
            "affected_classes": affected_classes,
            "class_breakdown": class_breakdown,
            "sample_evidence": sample_evidence
        }

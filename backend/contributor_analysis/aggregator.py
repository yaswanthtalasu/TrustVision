import json
from pathlib import Path
from typing import Dict, Any
import logging

from backend.config import (
    SCORE_EXACT_DUP_WEIGHT, SCORE_NEAR_DUP_WEIGHT,
    SCORE_LABEL_ANOMALY_WEIGHT, SCORE_TRIGGER_WEIGHT,
    SCORE_DISTRIBUTION_WEIGHT, SATURATION_EXACT_DUP_PCT,
    SATURATION_NEAR_DUP_PCT, SATURATION_LABEL_ANOMALY_PCT,
    SATURATION_TRIGGER_PCT, SATURATION_DISTRIBUTION_DRIFT,
    QUARANTINE_SCORE_THRESHOLD, REVIEW_SCORE_THRESHOLD
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustVision.Aggregator")


class ContributorAggregator:
    def __init__(self):
        pass

    def evaluate(self, evidence_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregates sample-level detector evidence into contributor-level risk metrics and decision.
        """
        contributor_id = evidence_package["contributor_id"]
        total_samples = evidence_package["total_samples"]
        detectors = evidence_package.get("detector_results", {})

        # 1. Extract detector metrics
        exact_res = detectors.get("exact_duplicate", {})
        near_res = detectors.get("near_duplicate", {})
        label_res = detectors.get("label_anomaly", {})
        dist_res = detectors.get("distribution_shift", {})
        trig_res = detectors.get("controlled_trigger", {})

        exact_count = exact_res.get("exact_duplicate_count", 0)
        exact_pct = exact_res.get("affected_percentage", 0.0)

        near_count = near_res.get("near_duplicate_affected_count", 0)
        near_pct = near_res.get("affected_percentage", 0.0)

        label_count = label_res.get("label_anomaly_count", 0)
        label_pct = label_res.get("affected_percentage", 0.0)

        trig_count = trig_res.get("trigger_count", 0)
        trig_pct = trig_res.get("affected_percentage", 0.0)

        dist_score = dist_res.get("distribution_difference_score", 0.0)
        dist_shift = dist_res.get("shift_detected", False)

        # 2. Calculate dynamic composite risk score (strictly bounded 0.0 - 100.0)
        exact_points = min(1.0, exact_pct / SATURATION_EXACT_DUP_PCT) * SCORE_EXACT_DUP_WEIGHT
        near_points = min(1.0, near_pct / SATURATION_NEAR_DUP_PCT) * SCORE_NEAR_DUP_WEIGHT
        label_points = min(1.0, label_pct / SATURATION_LABEL_ANOMALY_PCT) * SCORE_LABEL_ANOMALY_WEIGHT
        trig_points = min(1.0, trig_pct / SATURATION_TRIGGER_PCT) * SCORE_TRIGGER_WEIGHT
        dist_points = min(1.0, dist_score / SATURATION_DISTRIBUTION_DRIFT) * SCORE_DISTRIBUTION_WEIGHT

        risk_score = round(float(exact_points + near_points + label_points + trig_points + dist_points), 2)
        risk_score = min(max(risk_score, 0.0), 100.0)

        # 3. Transparent Rule-Based Decision Logic
        reasons = []
        if trig_count > 0:
            reasons.append(f"Synthetic pattern triggers detected ({trig_count} samples affected).")
        if label_pct >= 3.0:
            reasons.append(f"High visual label inconsistency ratio ({label_pct}% affected).")
        if exact_pct >= 2.0:
            reasons.append(f"Excessive exact duplicate flooding ({exact_pct}% affected).")
        if near_pct >= 5.0:
            reasons.append(f"Elevated near-duplicate image ratio ({near_pct}% affected).")
        if dist_shift:
            reasons.append(f"Significant class distribution shift detected (drift score: {dist_score}).")

        # Determine decision
        if risk_score >= QUARANTINE_SCORE_THRESHOLD or trig_count > 0 or label_pct >= 3.5:
            decision = "QUARANTINE"
            summary_statement = f"Contributor {contributor_id} contains significant integrity-risk evidence requiring quarantine."
        elif risk_score >= REVIEW_SCORE_THRESHOLD or dist_shift or near_pct >= 3.0:
            decision = "REVIEW"
            summary_statement = f"Contributor {contributor_id} exhibits moderate integrity anomalies warranting analyst review."
        else:
            decision = "ACCEPT"
            summary_statement = f"Contributor {contributor_id} meets integrity assurance baseline with negligible evidence indicators."
            if not reasons:
                reasons.append("No significant integrity risk evidence observed across all 5 detectors.")

        aggregation_result = {
            "contributor_id": contributor_id,
            "total_samples": total_samples,
            "decision": decision,
            "risk_score": risk_score,
            "summary_statement": summary_statement,
            "evidence_summary": {
                "exact_duplicates": {
                    "count": exact_count,
                    "affected_percentage": exact_pct
                },
                "near_duplicates": {
                    "count": near_count,
                    "affected_percentage": near_pct
                },
                "label_anomalies": {
                    "count": label_count,
                    "affected_percentage": label_pct
                },
                "synthetic_triggers": {
                    "count": trig_count,
                    "affected_percentage": trig_pct
                },
                "distribution_shift": {
                    "shift_detected": dist_shift,
                    "difference_score": dist_score
                }
            },
            "primary_risk_reasons": reasons
        }

        logger.info(f"Evaluated {contributor_id} -> Decision: {decision} (Risk Score: {risk_score})")
        return aggregation_result


if __name__ == "__main__":
    agg = ContributorAggregator()
    print("ContributorAggregator initialized.")

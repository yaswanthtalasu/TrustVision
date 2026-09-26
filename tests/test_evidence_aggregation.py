import pytest
from backend.contributor_analysis.aggregator import ContributorAggregator

def test_aggregator_decision_logic():
    aggregator = ContributorAggregator()

    # Clean contributor evidence simulation -> ACCEPT
    clean_package = {
        "contributor_id": "C1",
        "total_samples": 2000,
        "detector_results": {
            "exact_duplicate": {"exact_duplicate_count": 0, "affected_percentage": 0.0},
            "near_duplicate": {"near_duplicate_affected_count": 0, "affected_percentage": 0.0},
            "label_anomaly": {"label_anomaly_count": 0, "affected_percentage": 0.0},
            "distribution_shift": {"distribution_difference_score": 1.2, "shift_detected": False},
            "controlled_trigger": {"trigger_count": 0, "affected_percentage": 0.0}
        }
    }
    clean_res = aggregator.evaluate(clean_package)
    assert clean_res["decision"] == "ACCEPT"
    assert clean_res["risk_score"] < 10.0

    # Risky contributor evidence simulation -> QUARANTINE
    risky_package = {
        "contributor_id": "C3",
        "total_samples": 2000,
        "detector_results": {
            "exact_duplicate": {"exact_duplicate_count": 160, "affected_percentage": 8.0},
            "near_duplicate": {"near_duplicate_affected_count": 100, "affected_percentage": 5.0},
            "label_anomaly": {"label_anomaly_count": 80, "affected_percentage": 4.0},
            "distribution_shift": {"distribution_difference_score": 18.5, "shift_detected": True},
            "controlled_trigger": {"trigger_count": 60, "affected_percentage": 3.0}
        }
    }
    risky_res = aggregator.evaluate(risky_package)
    assert risky_res["decision"] == "QUARANTINE"
    assert risky_res["risk_score"] >= 30.0
    assert len(risky_res["primary_risk_reasons"]) >= 3

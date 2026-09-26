import json
import datetime
from pathlib import Path
from typing import Dict, Any, List
import logging

from backend.config import BASE_DIR, REPORTS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustVision.ReportGenerator")


class ReportGenerator:
    def __init__(self, reports_dir: Path = REPORTS_DIR):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_json_report(
        self,
        project_name: str,
        dataset_name: str,
        contributor_evaluations: List[Dict[str, Any]],
        crypto_manifests: Dict[str, Any] = None
    ) -> Path:
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        report_data = {
            "project": project_name,
            "dataset": dataset_name,
            "phase": "Data Integrity Assurance Phase",
            "timestamp": timestamp,
            "summary": {
                "total_contributors_analyzed": len(contributor_evaluations),
                "accept_count": sum(1 for c in contributor_evaluations if c["decision"] == "ACCEPT"),
                "review_count": sum(1 for c in contributor_evaluations if c["decision"] == "REVIEW"),
                "quarantine_count": sum(1 for c in contributor_evaluations if c["decision"] == "QUARANTINE")
            },
            "contributors": contributor_evaluations,
            "crypto_manifests": crypto_manifests or {},
            "limitations": [
                "The Controlled Trigger Detector is tuned for synthetic patch patterns used in test demonstrations.",
                "Perceptual hashing and feature embeddings detect visual similarity and label inconsistency, not malicious intent.",
                "Distribution shift analysis relies on clean CIFAR-10 reference class balance baseline."
            ]
        }

        output_file = self.reports_dir / "assurance_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"JSON assurance report saved to {output_file}")
        return output_file

    def generate_html_report(
        self,
        json_report_path: Path
    ) -> Path:
        with open(json_report_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        summary = data.get("summary", {})
        contributors = data.get("contributors", [])
        limitations = data.get("limitations", [])

        # Build HTML Rows
        contrib_rows = ""
        for c in contributors:
            cid = c["contributor_id"]
            decision = c["decision"]
            badge_color = (
                "#10B981" if decision == "ACCEPT" else
                "#F59E0B" if decision == "REVIEW" else
                "#EF4444"
            )
            score = c.get("risk_score", 0.0)
            ev = c.get("evidence_summary", {})
            exact = ev.get("exact_duplicates", {}).get("count", 0)
            near = ev.get("near_duplicates", {}).get("count", 0)
            label = ev.get("label_anomalies", {}).get("count", 0)
            trig = ev.get("synthetic_triggers", {}).get("count", 0)
            reasons = "<br/>".join(c.get("primary_risk_reasons", []))

            contrib_rows += f"""
            <tr style="border-bottom: 1px solid #E5E7EB;">
                <td style="padding: 12px; font-weight: bold; color: #1F2937;">{cid}</td>
                <td style="padding: 12px;">
                    <span style="background-color: {badge_color}; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;">
                        {decision}
                    </span>
                </td>
                <td style="padding: 12px; font-weight: 600; color: #374151;">{score} / 100</td>
                <td style="padding: 12px; font-size: 0.9rem; color: #4B5563;">
                    Exact: <b>{exact}</b> | Near: <b>{near}</b> | Label: <b>{label}</b> | Trigger: <b>{trig}</b>
                </td>
                <td style="padding: 12px; font-size: 0.85rem; color: #6B7280;">{reasons}</td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrustVision - Data Integrity Assurance Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #F9FAFB; color: #111827; margin: 0; padding: 24px; }}
        .container {{ max-width: 1100px; margin: 0 auto; background: white; padding: 32px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        h1 {{ color: #1E3A8A; font-size: 2rem; margin-bottom: 8px; font-weight: 800; }}
        .subtitle {{ color: #6B7280; font-size: 1rem; margin-bottom: 24px; border-bottom: 2px solid #E5E7EB; padding-bottom: 16px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }}
        .metric-card {{ background: #F3F4F6; padding: 16px; border-radius: 8px; text-align: center; border-left: 4px solid #3B82F6; }}
        .metric-value {{ font-size: 1.8rem; font-weight: 800; color: #1E3A8A; }}
        .metric-label {{ font-size: 0.85rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; margin-bottom: 32px; }}
        th {{ background: #F3F4F6; text-align: left; padding: 12px; font-size: 0.85rem; color: #374151; text-transform: uppercase; letter-spacing: 0.05em; }}
        .section-title {{ font-size: 1.25rem; font-weight: 700; color: #1F2937; margin-top: 24px; margin-bottom: 12px; }}
        .limitations-box {{ background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 16px; border-radius: 8px; margin-top: 24px; }}
        .limitations-box ul {{ margin: 8px 0 0 20px; padding: 0; color: #92400E; font-size: 0.9rem; }}
        .footer {{ text-align: center; color: #9CA3AF; font-size: 0.8rem; margin-top: 40px; border-top: 1px solid #E5E7EB; padding-top: 16px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ TrustVision Assurance Report</h1>
        <div class="subtitle">
            Project: <b>{data.get("project")}</b> | Dataset: <b>{data.get("dataset")}</b> | Generated: <b>{data.get("timestamp")}</b>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{summary.get("total_contributors_analyzed", 0)}</div>
                <div class="metric-label">Contributors Analyzed</div>
            </div>
            <div class="metric-card" style="border-left-color: #10B981;">
                <div class="metric-value" style="color: #065F46;">{summary.get("accept_count", 0)}</div>
                <div class="metric-label">ACCEPT</div>
            </div>
            <div class="metric-card" style="border-left-color: #F59E0B;">
                <div class="metric-value" style="color: #92400E;">{summary.get("review_count", 0)}</div>
                <div class="metric-label">REVIEW</div>
            </div>
            <div class="metric-card" style="border-left-color: #EF4444;">
                <div class="metric-value" style="color: #991B1B;">{summary.get("quarantine_count", 0)}</div>
                <div class="metric-label">QUARANTINE</div>
            </div>
        </div>

        <div class="section-title">Contributor Integrity Summary</div>
        <table>
            <thead>
                <tr>
                    <th>Contributor</th>
                    <th>Decision</th>
                    <th>Risk Score</th>
                    <th>Detector Evidence Summary</th>
                    <th>Primary Decision Rationale</th>
                </tr>
            </thead>
            <tbody>
                {contrib_rows}
            </tbody>
        </table>

        <div class="limitations-box">
            <strong style="color: #92400E;">⚠️ Assurance Framework Limitations & Scope</strong>
            <ul>
                {"".join([f"<li>{lim}</li>" for lim in limitations])}
            </ul>
        </div>

        <div class="footer">
            TrustVision Data Integrity Assurance Engine &bull; Cryptographically Verified SHA-256 Manifest Integration
        </div>
    </div>
</body>
</html>
"""

        output_file = self.reports_dir / "assurance_report.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML assurance report saved to {output_file}")
        return output_file


if __name__ == "__main__":
    rg = ReportGenerator()
    print("ReportGenerator initialized.")

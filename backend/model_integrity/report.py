import json
from pathlib import Path
from backend.config import REPORTS_DIR
from backend.model_integrity.schemas import VerificationResult

def generate_json_report(result: VerificationResult) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / f"model_integrity_{result.verification_id}.json"
    
    report = {
        "module": "Model Integrity",
        "check": "Model Artifact SHA-256 Verification",
        "algorithm": result.hash_algorithm,
        "result": {
            "claimed_hash": result.claimed_hash,
            "computed_hash": result.computed_hash,
            "match": result.match,
            "status": result.status
        },
        "interpretation": "The received model artifact matches the artifact represented by the supplied SHA-256." if result.match else "The received model artifact does not match the artifact represented by the supplied SHA-256.",
        "limitation": "A matching SHA-256 does not establish that the model itself is safe or free from malicious behavior."
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    return json_path

def generate_html_report(json_path: Path) -> Path:
    with open(json_path, "r", encoding="utf-8") as f:
        report = json.load(f)
        
    html_path = json_path.with_suffix(".html")
    match_status = "PASS" if report["result"]["match"] else "REVIEW"
    interpretation = report["interpretation"]
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Model Integrity Assurance Report</title>
        <style>
            body {{ font-family: sans-serif; margin: 2rem; }}
            .monospace {{ font-family: monospace; background: #f0f0f0; padding: 2px 4px; }}
            .pass {{ color: green; font-weight: bold; }}
            .review {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>TrustVision</h1>
        <h2>Model Integrity Assurance Report</h2>
        <hr>
        
        <h3>Verification Summary</h3>
        <p><strong>Hash Algorithm:</strong> {report['algorithm']}</p>
        <p><strong>Verification Status:</strong> <span class="{'pass' if report['result']['match'] else 'review'}">{match_status}</span></p>
        
        <h3>Cryptographic Evidence</h3>
        <p><strong>Company-provided SHA-256:</strong> <span class="monospace">{report['result']['claimed_hash']}</span></p>
        <p><strong>TrustVision-computed SHA-256:</strong> <span class="monospace">{report['result']['computed_hash']}</span></p>
        
        <h3>Result</h3>
        <p><strong>{match_status}</strong></p>
        <p>{interpretation}</p>
        
        <h3>Limitation</h3>
        <p><em>This check verifies artifact integrity against the supplied SHA-256. It does not establish model safety, correctness, accuracy, or absence of hidden behavior.</em></p>
    </body>
    </html>
    """
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    return html_path

def generate_behavioral_report(result) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / f"model_integrity_{result.analysis_id}.json"
    
    report = {
        "module": "Model Integrity",
        "check": "Behavioral Integrity Analysis",
        "algorithm": "N/A",
        "result": {
            "match": result.status == "PASS",
            "status": result.status,
            "claimed_hash": "N/A",
            "computed_hash": "N/A"
        },
        "behavioral": {
            "reference_model": result.reference_model,
            "submitted_model": result.submitted_model,
            "normal_test": result.normal_test,
            "trigger_test": result.trigger_test,
            "evidence": result.evidence
        },
        "interpretation": "Behavioral deviation detected under the controlled test suite. Further investigation is recommended." if result.status == "REVIEW" else "No significant behavioral deviation detected.",
        "limitations": result.limitations
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    return json_path

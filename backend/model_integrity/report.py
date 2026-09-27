import json
from pathlib import Path
from backend.config import REPORTS_DIR
from backend.model_integrity.schemas import VerificationResult, FullIntegrityResult

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

def generate_full_report(result: FullIntegrityResult) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / f"model_integrity_{result.verification_id}.json"
    
    report = {
        "module": "Model Integrity",
        "check": "Comprehensive Model Integrity Analysis",
        "timestamp": result.timestamp,
        "model_filename": result.model_filename,
        "overall_disposition": result.overall_disposition,
        "artifact": {
            "status": result.artifact.status,
            "claimed_hash": result.artifact.claimed_hash,
            "computed_hash": result.artifact.computed_hash,
            "match": result.artifact.match
        }
    }
    
    if result.behavioral:
        report["behavioral"] = {
            "status": result.behavioral.status,
            "reference_model": result.behavioral.reference_model,
            "normal_test": result.behavioral.normal_test,
            "trigger_test": result.behavioral.trigger_test,
            "evidence": result.behavioral.evidence,
            "limitations": result.behavioral.limitations
        }
    else:
        report["behavioral"] = None
        
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    return json_path

def generate_html_report(json_path: Path) -> Path:
    with open(json_path, "r", encoding="utf-8") as f:
        report = json.load(f)
        
    html_path = json_path.with_suffix(".html")
    
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
            .quarantine {{ color: darkorange; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>TrustVision</h1>
        <h2>Model Integrity Assurance Report</h2>
        <hr>
    """
    
    if report["check"] == "Comprehensive Model Integrity Analysis":
        disp = report["overall_disposition"]
        disp_class = "pass" if disp == "ACCEPT" else "review" if disp == "REVIEW" else "quarantine"
        
        html += f"""
        <h3>Overall Disposition: <span class="{disp_class}">{disp}</span></h3>
        <p><strong>Model:</strong> {report['model_filename']}</p>
        <p><strong>Timestamp:</strong> {report['timestamp']}</p>
        
        <hr>
        <h3>Artifact Integrity: <span class="{'pass' if report['artifact']['status'] == 'PASS' else 'review'}">{report['artifact']['status']}</span></h3>
        <p><strong>Company-provided SHA-256:</strong> <span class="monospace">{report['artifact']['claimed_hash']}</span></p>
        <p><strong>TrustVision-computed SHA-256:</strong> <span class="monospace">{report['artifact']['computed_hash']}</span></p>
        """
        
        if report.get("behavioral"):
            beh_stat = report["behavioral"]["status"]
            html += f"""
            <hr>
            <h3>Behavioral Integrity: <span class="{'pass' if beh_stat == 'PASS' else 'review'}">{beh_stat}</span></h3>
            <p><strong>Reference Model:</strong> {report["behavioral"]["reference_model"]}</p>
            <h4>Normal Test Suite</h4>
            <ul>
                <li>Agreement: {report['behavioral']['normal_test']['agreement']}</li>
                <li>Disagreement: {report['behavioral']['normal_test']['disagreement']}</li>
            </ul>
            <h4>Trigger Test Suite</h4>
            <ul>
                <li>Deviation Rate: {report['behavioral']['trigger_test']['deviation_rate']}</li>
            </ul>
            <h4>Evidence</h4>
            <ul>
                {"".join([f"<li>{ev}</li>" for ev in report['behavioral']['evidence']])}
            </ul>
            <h4>Limitations</h4>
            <ul>
                {"".join([f"<li>{lim}</li>" for lim in report['behavioral']['limitations']])}
            </ul>
            """
        else:
            html += """
            <hr>
            <h3>Behavioral Integrity</h3>
            <p>Could not execute behavioral analysis (Model failed to load or artifact check failed).</p>
            """
            
    else:
        # Fallback for old style reports if generated directly
        match_status = "PASS" if report["result"].get("match") else "REVIEW"
        html += f"""
        <h3>Verification Summary</h3>
        <p><strong>Hash Algorithm:</strong> {report.get('algorithm', 'SHA-256')}</p>
        <p><strong>Verification Status:</strong> <span class="{'pass' if match_status == 'PASS' else 'review'}">{match_status}</span></p>
        <p>{report.get('interpretation', '')}</p>
        """
        
    html += """
    </body>
    </html>
    """
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    return html_path

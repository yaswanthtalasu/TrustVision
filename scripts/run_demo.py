import sys
import os
import time
import json
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.data_manager import ReferenceDataManager
from backend.generator import ContributorGenerator
from backend.hashing import ManifestManager
from backend.evidence.engine import EvidenceEngine
from backend.contributor_analysis.aggregator import ContributorAggregator
from backend.reports.generator import ReportGenerator


def print_banner(text: str):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def run_demonstration():
    # Ensure UTF-8 output for Windows console compatibility
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print_banner("TRUSTVISION - DATA INTEGRITY ASSURANCE END-TO-END DEMONSTRATION")

    # STEP 1: Download / Verify CIFAR-10 Reference Data
    print_banner("STEP 1: Reference Dataset Management (CIFAR-10)")
    data_mgr = ReferenceDataManager()
    ref_manifest = data_mgr.download_and_extract(force=False)
    print(f"[OK] CIFAR-10 clean reference dataset active with {len(ref_manifest['samples'])} samples.")
    print("[OK] Cryptographic reference integrity check PASSED.")

    # STEP 2 & 3: Generate 4 Simulated Contributors
    print_banner("STEP 2 & 3: Generating Contributor Submissions (C1, C2, C3, C4)")
    generator = ContributorGenerator(seed=42, samples_per_contributor=1000)
    gen_results = generator.generate_all()

    print("\nContributor Configuration Summary:")
    print("  C1 → CLEAN (Correct image-label pairs, balanced distribution, no manipulation)")
    print("  C2 → CLEAN (Independent clean submission slice)")
    print("  C3 → RISKY (Controlled manipulated dataset: duplicates, near-dups, label swaps, trigger patch, shift)")
    print("  C4 → CLEAN (Independent clean submission slice)")

    # STEP 4 & 5 & 6: Submit to TrustVision Engine & Run Detectors
    print_banner("STEP 4, 5 & 6: Executing Data Integrity Detectors across Submissions")
    evidence_engine = EvidenceEngine()
    aggregator = ContributorAggregator()
    manifest_mgr = ManifestManager()

    evaluations = []
    crypto_manifests = {}

    for cid in ["C1", "C2", "C3", "C4"]:
        print(f"\n--- Analyzing Contributor Submission: {cid} ---")
        contrib_dir = BASE_DIR / "data" / "contributors" / ("C3_risky" if cid == "C3" else f"{cid}_clean")
        
        # Cryptographic SHA-256 Manifest
        c_manifest = manifest_mgr.create_contributor_manifest(cid, contrib_dir)
        crypto_manifests[cid] = c_manifest["dataset_root_hash"]

        # Run 5 Detectors
        start_t = time.time()
        ev_package = evidence_engine.analyze_contributor(cid, contrib_dir)
        duration = time.time() - start_t

        # Aggregation Decision
        eval_res = aggregator.evaluate(ev_package)
        evaluations.append(eval_res)

        print(f"  Analysis Completed in {duration:.2f}s")
        print(f"  Total Samples Analyzed: {eval_res['total_samples']}")
        print(f"  Calculated Risk Score:  {eval_res['risk_score']} / 100")
        print(f"  DECISION STATE:         [{eval_res['decision']}]")

        # STEP 7: Show C3 accumulating evidence from all 5 detectors
        if cid == "C3":
            print_banner("STEP 7: Detailed Evidence Breakdown for Contributor C3")
            ev_sum = eval_res["evidence_summary"]
            print(f"  1. Exact Duplicate Flooding: {ev_sum['exact_duplicates']['count']} samples ({ev_sum['exact_duplicates']['affected_percentage']}%)")
            print(f"  2. Near-Duplicate Augments: {ev_sum['near_duplicates']['count']} samples ({ev_sum['near_duplicates']['affected_percentage']}%)")
            print(f"  3. Visual Label Inconsistency: {ev_sum['label_anomalies']['count']} samples ({ev_sum['label_anomalies']['affected_percentage']}%)")
            print(f"  4. Synthetic Patch Triggers: {ev_sum['synthetic_triggers']['count']} samples ({ev_sum['synthetic_triggers']['affected_percentage']}%)")
            print(f"  5. Class Distribution Drift: Shift Detected={ev_sum['distribution_shift']['shift_detected']} (Drift Score: {ev_sum['distribution_shift']['difference_score']})")

    # STEP 8 & 9: Aggregate & Final Decision Matrix
    print_banner("STEP 8 & 9: Pipeline Evidence Aggregation & Decision Matrix")
    print(f"{'Contributor':<15} {'Decision':<15} {'Risk Score':<15} {'Root Hash (SHA-256)':<25}")
    print("-" * 75)
    for e in evaluations:
        cid = e["contributor_id"]
        dec = e["decision"]
        score = e["risk_score"]
        r_hash = crypto_manifests[cid][:20] + "..."
        print(f"{cid:<15} {dec:<15} {score:<15} {r_hash:<25}")

    # STEP 10: Generate JSON and HTML Assurance Reports
    print_banner("STEP 10: Assurance Report Generation")
    report_gen = ReportGenerator()
    json_path = report_gen.generate_json_report("TrustVision", "CIFAR-10", evaluations, crypto_manifests)
    html_path = report_gen.generate_html_report(json_path)

    print(f"[OK] Machine-readable JSON Report saved to: {json_path}")
    print(f"[OK] Standalone Human-readable HTML Report saved to: {html_path}")
    print("\nDemonstration complete! Run `uvicorn backend.api.main:app` and start the frontend to view the dashboard.")


if __name__ == "__main__":
    run_demonstration()

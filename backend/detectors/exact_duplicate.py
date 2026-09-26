import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List
from backend.config import BASE_DIR, EXACT_DUP_SEVERITY_THRESHOLD
from backend.detectors.base import BaseDetector


class ExactDuplicateDetector(BaseDetector):
    def __init__(self):
        super().__init__(
            name="exact_duplicate",
            description="Identifies exact byte-level image duplicates using SHA-256 cryptographic hashes."
        )

    def analyze(self, contributor_id: str, contrib_dir: Path, ref_manifest: Dict[str, Any]) -> Dict[str, Any]:
        contrib_dir = Path(contrib_dir)
        manifest_file = contrib_dir / "manifest.json"

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        samples = manifest.get("samples", [])
        total_samples = len(samples)

        # Hash map: sha256 -> list of sample_ids
        hash_map: Dict[str, List[str]] = {}
        sample_hash_lookup: Dict[str, str] = {}

        for sample in samples:
            sample_id = sample["sample_id"]
            img_path = BASE_DIR / sample["file_path"]

            if img_path.exists():
                with open(img_path, "rb") as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
            else:
                file_hash = sample.get("sha256", "")

            sample_hash_lookup[sample_id] = file_hash
            if file_hash not in hash_map:
                hash_map[file_hash] = []
            hash_map[file_hash].append(sample_id)

        # Identify duplicate groups
        duplicate_groups = {}
        exact_dup_samples_count = 0
        sample_evidence = []
        group_counter = 1

        for file_hash, sample_ids in hash_map.items():
            if len(sample_ids) > 1:
                group_id = f"DG_{group_counter:03d}"
                group_counter += 1
                dup_count = len(sample_ids)
                exact_dup_samples_count += (dup_count - 1)

                duplicate_groups[group_id] = {
                    "hash": file_hash[:12],
                    "count": dup_count,
                    "sample_ids": sample_ids
                }

                severity = "HIGH" if dup_count > 3 else "MEDIUM"

                for sid in sample_ids:
                    sample_evidence.append({
                        "detector": self.name,
                        "contributor_id": contributor_id,
                        "sample_id": sid,
                        "evidence": {
                            "duplicate_group": group_id,
                            "duplicate_count": dup_count,
                            "hash_prefix": file_hash[:12]
                        },
                        "severity": severity,
                        "description": f"Exact duplicate image detected in group {group_id} ({dup_count} instances)."
                    })

        affected_percentage = (exact_dup_samples_count / total_samples * 100.0) if total_samples > 0 else 0.0

        return {
            "detector": self.name,
            "contributor_id": contributor_id,
            "total_samples": total_samples,
            "duplicate_groups_count": len(duplicate_groups),
            "exact_duplicate_count": exact_dup_samples_count,
            "affected_percentage": round(affected_percentage, 2),
            "duplicate_groups": duplicate_groups,
            "sample_evidence": sample_evidence
        }

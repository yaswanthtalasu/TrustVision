import json
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image
import imagehash
from backend.config import BASE_DIR, NEAR_DUP_PHASH_THRESHOLD
from backend.detectors.base import BaseDetector


class NearDuplicateDetector(BaseDetector):
    def __init__(self, phash_threshold: int = NEAR_DUP_PHASH_THRESHOLD):
        super().__init__(
            name="near_duplicate",
            description="Identifies visually similar near-duplicate images using perceptual hashing (pHash)."
        )
        self.phash_threshold = phash_threshold

    def analyze(self, contributor_id: str, contrib_dir: Path, ref_manifest: Dict[str, Any]) -> Dict[str, Any]:
        contrib_dir = Path(contrib_dir)
        manifest_file = contrib_dir / "manifest.json"

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        samples = manifest.get("samples", [])
        total_samples = len(samples)

        # Calculate pHash & exact sha256 for each sample
        hashes = []
        sha_set = set()

        for s in samples:
            img_path = BASE_DIR / s["file_path"]
            if img_path.exists():
                img = Image.open(img_path)
                ph = imagehash.phash(img)
                sha = s.get("sha256", "")
            else:
                ph = None
                sha = ""
            hashes.append({
                "sample_id": s["sample_id"],
                "phash": ph,
                "sha256": sha
            })

        near_dup_pairs = []
        affected_sample_ids = set()
        sample_evidence = []

        # Pairwise comparison (optimizable via BK-tree or spatial hashing for larger datasets)
        n = len(hashes)
        for i in range(n):
            if hashes[i]["phash"] is None:
                continue
            for j in range(i + 1, n):
                if hashes[j]["phash"] is None:
                    continue

                # Skip exact byte duplicates (handled by exact duplicate detector)
                if hashes[i]["sha256"] and hashes[i]["sha256"] == hashes[j]["sha256"]:
                    continue

                dist = hashes[i]["phash"] - hashes[j]["phash"]
                if dist <= self.phash_threshold:
                    sid_a = hashes[i]["sample_id"]
                    sid_b = hashes[j]["sample_id"]

                    similarity_score = round(1.0 - (dist / 64.0), 3)

                    near_dup_pairs.append({
                        "sample_a": sid_a,
                        "sample_b": sid_b,
                        "hamming_distance": int(dist),
                        "similarity_score": similarity_score
                    })

                    affected_sample_ids.add(sid_a)
                    affected_sample_ids.add(sid_b)

        # Generate sample level evidence
        for sid in sorted(affected_sample_ids):
            # Find related pairs
            related = [p for p in near_dup_pairs if p["sample_a"] == sid or p["sample_b"] == sid]
            min_dist = min([p["hamming_distance"] for p in related])
            max_sim = max([p["similarity_score"] for p in related])

            sample_evidence.append({
                "detector": self.name,
                "contributor_id": contributor_id,
                "sample_id": sid,
                "evidence": {
                    "related_pairs_count": len(related),
                    "min_hamming_distance": min_dist,
                    "max_similarity_score": max_sim,
                    "sample_pairs": [p["sample_b"] if p["sample_a"] == sid else p["sample_a"] for p in related[:3]]
                },
                "severity": "MEDIUM",
                "description": f"Near-duplicate evidence detected. Visually similar to {len(related)} sample(s) (sim: {max_sim})."
            })

        affected_count = len(affected_sample_ids)
        affected_percentage = (affected_count / total_samples * 100.0) if total_samples > 0 else 0.0

        return {
            "detector": self.name,
            "contributor_id": contributor_id,
            "total_samples": total_samples,
            "near_duplicate_pairs_count": len(near_dup_pairs),
            "near_duplicate_affected_count": affected_count,
            "affected_percentage": round(affected_percentage, 2),
            "threshold_used": self.phash_threshold,
            "near_dup_pairs": near_dup_pairs[:50],  # cap list for report brevity
            "sample_evidence": sample_evidence
        }

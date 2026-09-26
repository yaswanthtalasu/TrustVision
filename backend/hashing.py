import os
import json
import hashlib
from pathlib import Path
import logging
from backend.config import BASE_DIR, MANIFESTS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustVision.Hashing")


class ManifestManager:
    def __init__(self, manifests_dir: Path = MANIFESTS_DIR):
        self.manifests_dir = Path(manifests_dir)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)

    def generate_file_sha256(self, filepath: Path) -> str:
        """
        Calculates SHA-256 checksum of a file.
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_contributor_manifest(self, contributor_id: str, contrib_dir: Path) -> dict:
        """
        Creates a cryptographic SHA-256 manifest for a contributor dataset.
        """
        contrib_dir = Path(contrib_dir)
        manifest_file = contrib_dir / "manifest.json"
        
        if not manifest_file.exists():
            raise FileNotFoundError(f"Manifest not found for contributor {contributor_id} at {manifest_file}")

        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        manifest_entries = []
        for sample in data.get("samples", []):
            filepath = BASE_DIR / sample["file_path"]
            actual_sha256 = self.generate_file_sha256(filepath) if filepath.exists() else sample.get("sha256", "")
            
            entry = {
                "sample_id": sample["sample_id"],
                "file_path": sample["file_path"],
                "submitted_label": sample["submitted_label"],
                "sha256": actual_sha256
            }
            manifest_entries.append(entry)

        # Compute root Merkle/combined hash of dataset
        combined_hashes = "".join([e["sha256"] for e in manifest_entries])
        root_hash = hashlib.sha256(combined_hashes.encode("utf-8")).hexdigest()

        crypto_manifest = {
            "contributor_id": contributor_id,
            "dataset_root_hash": root_hash,
            "total_samples": len(manifest_entries),
            "samples": manifest_entries
        }

        output_path = self.manifests_dir / f"{contributor_id}_manifest.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(crypto_manifest, f, indent=2)

        logger.info(f"Generated cryptographic manifest for {contributor_id} with root hash {root_hash[:12]}...")
        return crypto_manifest

    def verify_manifest(self, manifest_path: Path) -> bool:
        """
        Verifies every file in the manifest matches its recorded SHA-256 checksum.
        """
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for sample in manifest.get("samples", []):
            filepath = BASE_DIR / sample["file_path"]
            if not filepath.exists():
                logger.error(f"Verification failed: missing file {filepath}")
                return False
            actual_hash = self.generate_file_sha256(filepath)
            if actual_hash != sample["sha256"]:
                logger.error(f"Checksum failure on {sample['sample_id']}: expected {sample['sha256']}, got {actual_hash}")
                return False

        logger.info(f"Manifest verification PASSED for {manifest_path.name}")
        return True


if __name__ == "__main__":
    mm = ManifestManager()
    print("ManifestManager initialized.")

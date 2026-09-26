import os
import json
import hashlib
import logging
from pathlib import Path
from PIL import Image
import torchvision.datasets as datasets
from backend.config import REFERENCE_DIR, CIFAR10_CLASSES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustVision.DataManager")


class ReferenceDataManager:
    def __init__(self, target_dir: Path = REFERENCE_DIR):
        self.target_dir = Path(target_dir)
        self.raw_dir = self.target_dir / "raw"
        self.images_dir = self.target_dir / "images"
        self.manifest_path = self.target_dir / "reference_manifest.json"

    def download_and_extract(self, force: bool = False) -> dict:
        """
        Downloads CIFAR-10 using torchvision and prepares clean reference image files & manifest.
        """
        if self.manifest_path.exists() and not force:
            logger.info("CIFAR-10 reference dataset already exists. Loading manifest...")
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)

        logger.info(f"Downloading official CIFAR-10 dataset into {self.raw_dir}...")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        cifar_dataset = datasets.CIFAR10(root=str(self.raw_dir), train=True, download=True)

        manifest = {
            "dataset": "CIFAR-10",
            "total_samples": len(cifar_dataset),
            "classes": CIFAR10_CLASSES,
            "samples": []
        }

        logger.info("Saving reference images and computing cryptographic hashes...")
        for idx, (img, label_idx) in enumerate(cifar_dataset):
            sample_id = f"REF_{idx:05d}"
            filename = f"{sample_id}.png"
            filepath = self.images_dir / filename

            # Save PNG image
            img.save(filepath, format="PNG")

            # Calculate SHA-256 hash of image file
            with open(filepath, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            sample_entry = {
                "sample_id": sample_id,
                "file_path": str(filepath.relative_to(self.target_dir.parent.parent)),
                "label_id": int(label_idx),
                "label_name": CIFAR10_CLASSES[label_idx],
                "sha256": file_hash
            }
            manifest["samples"].append(sample_entry)

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Successfully processed {len(manifest['samples'])} reference samples into {self.target_dir}")
        return manifest

    def load_manifest(self) -> dict:
        if not self.manifest_path.exists():
            return self.download_and_extract()
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def verify_integrity(self) -> bool:
        """
        Verifies that no reference image has been tampered with.
        """
        if not self.manifest_path.exists():
            logger.error("Manifest missing, cannot verify reference dataset integrity.")
            return False

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for sample in manifest["samples"]:
            filepath = self.target_dir.parent.parent / sample["file_path"]
            if not filepath.exists():
                logger.error(f"Missing reference file: {filepath}")
                return False
            with open(filepath, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            if current_hash != sample["sha256"]:
                logger.error(f"Hash mismatch for {sample['sample_id']}: expected {sample['sha256']}, got {current_hash}")
                return False

        logger.info("Reference dataset integrity check PASSED.")
        return True


if __name__ == "__main__":
    manager = ReferenceDataManager()
    manifest = manager.download_and_extract()
    print(f"Downloaded {len(manifest['samples'])} images.")

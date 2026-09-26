import os
import json
import random
import hashlib
import numpy as np
from pathlib import Path
from PIL import Image, ImageEnhance
import logging
from backend.config import (
    CONTRIBUTORS_DIR, CIFAR10_CLASSES, DEFAULT_SEED,
    DEFAULT_SAMPLES_PER_CONTRIBUTOR, TRIGGER_PATCH_SIZE,
    TRIGGER_PATCH_COLOR, TRIGGER_LOCATION
)
from backend.data_manager import ReferenceDataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrustVision.Generator")


class ContributorGenerator:
    def __init__(self, seed: int = DEFAULT_SEED, samples_per_contributor: int = DEFAULT_SAMPLES_PER_CONTRIBUTOR):
        self.seed = seed
        self.samples_per_contributor = samples_per_contributor
        self.ref_manager = ReferenceDataManager()

    def set_seed(self, seed: int):
        random.seed(seed)
        np.random.seed(seed)

    def _apply_near_duplicate_transform(self, img: Image.Image, trans_type: int) -> Image.Image:
        """
        Applies controlled PIL visual transformations:
        0: Slight brightness adjustment (+15%)
        1: Small rotation (+8 degrees)
        2: Small crop and resize
        3: Slight contrast shift
        """
        img_copy = img.copy()
        if trans_type == 0:
            enhancer = ImageEnhance.Brightness(img_copy)
            return enhancer.enhance(1.20)
        elif trans_type == 1:
            return img_copy.rotate(8, resample=Image.BICUBIC)
        elif trans_type == 2:
            w, h = img_copy.size
            crop_box = (2, 2, w - 2, h - 2)
            cropped = img_copy.crop(crop_box)
            return cropped.resize((w, h), Image.BICUBIC)
        else:
            enhancer = ImageEnhance.Contrast(img_copy)
            return enhancer.enhance(1.25)

    def _apply_trigger_patch(self, img: Image.Image) -> Image.Image:
        """
        Adds a controlled, visible synthetic 6x6 pixel square patch at top-left corner (2,2).
        """
        img_copy = img.copy().convert("RGB")
        x, y = TRIGGER_LOCATION
        w, h = img_copy.size
        pw, ph = TRIGGER_PATCH_SIZE, TRIGGER_PATCH_SIZE

        # Draw magenta square patch
        pixels = img_copy.load()
        for i in range(x, min(x + pw, w)):
            for j in range(y, min(y + ph, h)):
                pixels[i, j] = TRIGGER_PATCH_COLOR
        return img_copy

    def generate_all(self, force: bool = True) -> dict:
        self.set_seed(self.seed)
        ref_manifest = self.ref_manager.load_manifest()
        ref_samples = ref_manifest["samples"]
        total_ref = len(ref_samples)

        results = {}

        # Partition reference samples across 4 contributors cleanly first
        indices = list(range(total_ref))
        random.shuffle(indices)

        chunk_size = min(self.samples_per_contributor, total_ref // 4)
        c1_indices = indices[0:chunk_size]
        c2_indices = indices[chunk_size:2*chunk_size]
        c3_indices = indices[2*chunk_size:3*chunk_size]
        c4_indices = indices[3*chunk_size:4*chunk_size]

        # Generate C1 (Clean)
        results["C1"] = self._generate_contributor(
            contributor_id="C1",
            dataset_name="CIFAR10_C1_Clean",
            indices=c1_indices,
            ref_samples=ref_samples,
            is_manipulated=False
        )

        # Generate C2 (Clean)
        results["C2"] = self._generate_contributor(
            contributor_id="C2",
            dataset_name="CIFAR10_C2_Clean",
            indices=c2_indices,
            ref_samples=ref_samples,
            is_manipulated=False
        )

        # Generate C3 (Risky / Manipulated)
        results["C3"] = self._generate_c3_manipulated(
            contributor_id="C3",
            dataset_name="CIFAR10_C3_Risky",
            base_indices=c3_indices,
            ref_samples=ref_samples
        )

        # Generate C4 (Clean)
        results["C4"] = self._generate_contributor(
            contributor_id="C4",
            dataset_name="CIFAR10_C4_Clean",
            indices=c4_indices,
            ref_samples=ref_samples,
            is_manipulated=False
        )

        logger.info("Successfully generated all 4 contributor datasets (C1, C2, C3, C4).")
        return results

    def _generate_contributor(
        self,
        contributor_id: str,
        dataset_name: str,
        indices: list,
        ref_samples: list,
        is_manipulated: bool = False
    ) -> dict:
        contrib_dir = CONTRIBUTORS_DIR / f"{contributor_id}_{'risky' if is_manipulated else 'clean'}"
        images_dir = contrib_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        samples_meta = []
        for seq_id, idx in enumerate(indices):
            ref_sample = ref_samples[idx]
            ref_img_path = self.ref_manager.target_dir.parent.parent / ref_sample["file_path"]
            img = Image.open(ref_img_path)

            sample_name = f"{contributor_id}_{seq_id:05d}.png"
            dest_path = images_dir / sample_name
            img.save(dest_path, format="PNG")

            with open(dest_path, "rb") as f:
                img_hash = hashlib.sha256(f.read()).hexdigest()

            sample_entry = {
                "sample_id": f"{contributor_id}_{seq_id:05d}",
                "file_path": str(dest_path.relative_to(self.ref_manager.target_dir.parent.parent)),
                "submitted_label": ref_sample["label_name"],
                "submitted_label_id": ref_sample["label_id"],
                "reference_label": ref_sample["label_name"],
                "reference_label_id": ref_sample["label_id"],
                "ref_sample_id": ref_sample["sample_id"],
                "sha256": img_hash,
                "is_manipulated": False,
                "manipulations": []
            }
            samples_meta.append(sample_entry)

        # Metadata
        metadata = {
            "contributor_id": contributor_id,
            "dataset_name": dataset_name,
            "source_dataset": "CIFAR-10",
            "sample_count": len(samples_meta),
            "seed": self.seed,
            "manipulation": {
                "duplicate_flooding": False,
                "near_duplicates": False,
                "label_anomalies": False,
                "controlled_trigger": False,
                "distribution_shift": False
            }
        }

        with open(contrib_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        with open(contrib_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump({"samples": samples_meta}, f, indent=2)

        return metadata

    def _generate_c3_manipulated(
        self,
        contributor_id: str,
        dataset_name: str,
        base_indices: list,
        ref_samples: list
    ) -> dict:
        contrib_dir = CONTRIBUTORS_DIR / "C3_risky"
        images_dir = contrib_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        samples_meta = []
        seq_counter = 0

        # E. Class Distribution Shift: Over-sample class 0 (airplane), under-sample class 6 (frog)
        class_buckets = {i: [] for i in range(10)}
        for idx in base_indices:
            lbl = ref_samples[idx]["label_id"]
            class_buckets[lbl].append(idx)

        # Create distribution shift in selected indices
        shifted_indices = []
        # Skew: Multiply class 0 samples by 3.5x, class 1 by 2x, drop 80% of class 6
        for c_id in range(10):
            items = class_buckets[c_id]
            if c_id == 0:
                shifted_indices.extend(items * 3 + items[:len(items)//2])
            elif c_id == 1:
                shifted_indices.extend(items * 2)
            elif c_id == 6:
                shifted_indices.extend(items[:max(1, len(items)//5)])
            else:
                shifted_indices.extend(items)

        random.shuffle(shifted_indices)
        selected_indices = shifted_indices[:self.samples_per_contributor]

        # Select index subsets for specific controlled manipulations
        total_selected = len(selected_indices)
        
        # A. Duplicate flooding subset (e.g., 40 base samples duplicated 5 times = 200 total samples)
        dup_base_indices = selected_indices[:40]

        # B. Near duplicate subset (e.g., 50 samples transformed)
        near_dup_base_indices = selected_indices[40:90]

        # C. Label anomaly subset (e.g., 80 samples with swapped labels)
        label_anomaly_indices = set(selected_indices[90:170])

        # D. Trigger patch subset (e.g., 60 samples with patch injected)
        trigger_indices = set(selected_indices[170:230])

        # Generate base samples
        for idx in selected_indices:
            ref_sample = ref_samples[idx]
            ref_img_path = self.ref_manager.target_dir.parent.parent / ref_sample["file_path"]
            img = Image.open(ref_img_path)

            submitted_lbl_id = ref_sample["label_id"]
            submitted_lbl_name = ref_sample["label_name"]
            manipulations = []

            # C. Label Anomaly
            if idx in label_anomaly_indices:
                # Swap label to a wrong class
                new_lbl_id = (submitted_lbl_id + random.randint(1, 9)) % 10
                submitted_lbl_id = new_lbl_id
                submitted_lbl_name = CIFAR10_CLASSES[new_lbl_id]
                manipulations.append("label_anomaly")

            # D. Synthetic Trigger Patch
            if idx in trigger_indices:
                img = self._apply_trigger_patch(img)
                manipulations.append("controlled_trigger")

            sample_name = f"{contributor_id}_{seq_counter:05d}.png"
            dest_path = images_dir / sample_name
            img.save(dest_path, format="PNG")

            with open(dest_path, "rb") as f:
                img_hash = hashlib.sha256(f.read()).hexdigest()

            sample_entry = {
                "sample_id": f"{contributor_id}_{seq_counter:05d}",
                "file_path": str(dest_path.relative_to(self.ref_manager.target_dir.parent.parent)),
                "submitted_label": submitted_lbl_name,
                "submitted_label_id": submitted_lbl_id,
                "reference_label": ref_sample["label_name"],
                "reference_label_id": ref_sample["label_id"],
                "ref_sample_id": ref_sample["sample_id"],
                "sha256": img_hash,
                "is_manipulated": len(manipulations) > 0,
                "manipulations": manipulations
            }
            samples_meta.append(sample_entry)
            seq_counter += 1

        # A. Insert Exact Duplicate Flooding
        for dup_idx in dup_base_indices:
            ref_sample = ref_samples[dup_idx]
            ref_img_path = self.ref_manager.target_dir.parent.parent / ref_sample["file_path"]
            img = Image.open(ref_img_path)

            # Generate 4 exact copies
            for copy_n in range(4):
                sample_name = f"{contributor_id}_{seq_counter:05d}.png"
                dest_path = images_dir / sample_name
                img.save(dest_path, format="PNG")

                with open(dest_path, "rb") as f:
                    img_hash = hashlib.sha256(f.read()).hexdigest()

                sample_entry = {
                    "sample_id": f"{contributor_id}_{seq_counter:05d}",
                    "file_path": str(dest_path.relative_to(self.ref_manager.target_dir.parent.parent)),
                    "submitted_label": ref_sample["label_name"],
                    "submitted_label_id": ref_sample["label_id"],
                    "reference_label": ref_sample["label_name"],
                    "reference_label_id": ref_sample["label_id"],
                    "ref_sample_id": ref_sample["sample_id"],
                    "sha256": img_hash,
                    "is_manipulated": True,
                    "manipulations": ["duplicate_flooding"]
                }
                samples_meta.append(sample_entry)
                seq_counter += 1

        # B. Insert Near-Duplicates (Augmentations)
        for near_idx in near_dup_base_indices:
            ref_sample = ref_samples[near_idx]
            ref_img_path = self.ref_manager.target_dir.parent.parent / ref_sample["file_path"]
            img = Image.open(ref_img_path)

            for trans_id in range(2):
                transformed_img = self._apply_near_duplicate_transform(img, trans_id)
                sample_name = f"{contributor_id}_{seq_counter:05d}.png"
                dest_path = images_dir / sample_name
                transformed_img.save(dest_path, format="PNG")

                with open(dest_path, "rb") as f:
                    img_hash = hashlib.sha256(f.read()).hexdigest()

                sample_entry = {
                    "sample_id": f"{contributor_id}_{seq_counter:05d}",
                    "file_path": str(dest_path.relative_to(self.ref_manager.target_dir.parent.parent)),
                    "submitted_label": ref_sample["label_name"],
                    "submitted_label_id": ref_sample["label_id"],
                    "reference_label": ref_sample["label_name"],
                    "reference_label_id": ref_sample["label_id"],
                    "ref_sample_id": ref_sample["sample_id"],
                    "sha256": img_hash,
                    "is_manipulated": True,
                    "manipulations": ["near_duplicates"]
                }
                samples_meta.append(sample_entry)
                seq_counter += 1

        # Shuffle C3 dataset to interleave duplicates & anomalies realistic
        random.shuffle(samples_meta)

        metadata = {
            "contributor_id": contributor_id,
            "dataset_name": dataset_name,
            "source_dataset": "CIFAR-10",
            "sample_count": len(samples_meta),
            "seed": self.seed,
            "manipulation": {
                "duplicate_flooding": True,
                "near_duplicates": True,
                "label_anomalies": True,
                "controlled_trigger": True,
                "distribution_shift": True
            }
        }

        with open(contrib_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        with open(contrib_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump({"samples": samples_meta}, f, indent=2)

        return metadata


if __name__ == "__main__":
    generator = ContributorGenerator()
    res = generator.generate_all()
    print("Generation complete:", res)

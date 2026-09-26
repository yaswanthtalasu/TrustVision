import os
import json
import zipfile
import shutil
import random
import hashlib
import numpy as np
from pathlib import Path
from PIL import Image, ImageEnhance

BASE_DIR = Path(__file__).resolve().parent.parent
REF_MANIFEST_PATH = BASE_DIR / "data" / "reference" / "cifar10" / "reference_manifest.json"
OUTPUT_DIR = BASE_DIR / "data" / "risky_test_dataset"
ZIP_OUTPUT_PATH = BASE_DIR / "risky_test_dataset.zip"

CIFAR10_CLASSES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck"
]


def apply_near_dup_transform(img: Image.Image, trans_type: int) -> Image.Image:
    img_copy = img.copy()
    if trans_type == 0:
        enhancer = ImageEnhance.Brightness(img_copy)
        return enhancer.enhance(1.25)
    elif trans_type == 1:
        return img_copy.rotate(10, resample=Image.BICUBIC)
    elif trans_type == 2:
        w, h = img_copy.size
        crop_box = (2, 2, w - 2, h - 2)
        return img_copy.crop(crop_box).resize((w, h), Image.BICUBIC)
    else:
        enhancer = ImageEnhance.Contrast(img_copy)
        return enhancer.enhance(1.30)


def apply_trigger_patch(img: Image.Image) -> Image.Image:
    img_copy = img.copy().convert("RGB")
    pixels = img_copy.load()
    w, h = img_copy.size
    for i in range(2, min(8, w)):
        for j in range(2, min(8, h)):
            pixels[i, j] = (255, 0, 255)  # Magenta square
    return img_copy


def generate_risky_zip():
    print("=" * 70)
    print("  GENERATING RISKY TEST DATASET ZIP WITH ALL 4 INTEGRITY ERRORS")
    print("=" * 70)

    if not REF_MANIFEST_PATH.exists():
        print("Reference dataset missing. Downloading CIFAR-10 reference data first...")
        from backend.data_manager import ReferenceDataManager
        ReferenceDataManager().download_and_extract()

    with open(REF_MANIFEST_PATH, "r", encoding="utf-8") as f:
        ref_manifest = json.load(f)

    ref_samples = ref_manifest["samples"]
    
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    random.seed(42)
    indices = list(range(len(ref_samples)))
    random.shuffle(indices)

    samples_meta = []
    seq_counter = 0

    # Select base subsets for controlled errors
    base_samples = indices[:300]
    
    # 1. Exact Duplicate Flooding subset (20 base images x 3 copies = 60 extra duplicate samples)
    dup_subset = set(base_samples[:20])

    # 2. Near Duplicate subset (30 base images transformed)
    near_dup_subset = base_samples[20:50]

    # 3. Wrong Labelling / Label Mismatch subset (40 base images)
    wrong_label_subset = set(base_samples[50:90])

    # 4. Controlled Trigger Patch subset (30 base images)
    trigger_subset = set(base_samples[90:120])

    for idx in base_samples:
        ref_s = ref_samples[idx]
        ref_img_path = BASE_DIR / "data" / "reference" / "cifar10" / "images" / f"{ref_s['sample_id']}.png"
        if not ref_img_path.exists():
            ref_img_path = BASE_DIR / ref_s["file_path"]
        img = Image.open(ref_img_path)

        submitted_lbl_id = ref_s["label_id"]
        submitted_lbl_name = ref_s["label_name"]
        manipulations = []

        # Error Type 3: Wrong Labelling
        if idx in wrong_label_subset:
            wrong_id = (submitted_lbl_id + random.randint(1, 9)) % 10
            submitted_lbl_id = wrong_id
            submitted_lbl_name = CIFAR10_CLASSES[wrong_id]
            manipulations.append("wrong_labelling")

        # Error Type 4: Controlled Trigger Patch
        if idx in trigger_subset:
            img = apply_trigger_patch(img)
            manipulations.append("controlled_trigger_patch")

        sample_name = f"TEST_{seq_counter:05d}.png"
        dest_path = images_dir / sample_name
        img.save(dest_path, format="PNG")

        with open(dest_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        samples_meta.append({
            "sample_id": f"TEST_{seq_counter:05d}",
            "file_path": f"images/{sample_name}",
            "submitted_label": submitted_lbl_name,
            "submitted_label_id": submitted_lbl_id,
            "reference_label": ref_s["label_name"],
            "reference_label_id": ref_s["label_id"],
            "sha256": file_hash,
            "is_manipulated": len(manipulations) > 0,
            "manipulations": manipulations
        })
        seq_counter += 1

    # Error Type 1: Insert Exact Duplicate Flooding
    print("[1/4] Injecting Exact Duplicate Flooding (20 images duplicated 3x)...")
    for dup_idx in dup_subset:
        ref_s = ref_samples[dup_idx]
        ref_img_path = BASE_DIR / "data" / "reference" / "cifar10" / "images" / f"{ref_s['sample_id']}.png"
        if not ref_img_path.exists():
            ref_img_path = BASE_DIR / ref_s["file_path"]
        img = Image.open(ref_img_path)

        for copy_i in range(3):
            sample_name = f"TEST_{seq_counter:05d}.png"
            dest_path = images_dir / sample_name
            img.save(dest_path, format="PNG")

            with open(dest_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            samples_meta.append({
                "sample_id": f"TEST_{seq_counter:05d}",
                "file_path": f"images/{sample_name}",
                "submitted_label": ref_s["label_name"],
                "submitted_label_id": ref_s["label_id"],
                "reference_label": ref_s["label_name"],
                "reference_label_id": ref_s["label_id"],
                "sha256": file_hash,
                "is_manipulated": True,
                "manipulations": ["exact_duplicate_flooding"]
            })
            seq_counter += 1

    # Error Type 2: Insert Near-Duplicates (Visual Augmentations)
    print("[2/4] Injecting Near-Duplicate Visual Augmentations (30 images transformed)...")
    for near_idx in near_dup_subset:
        ref_s = ref_samples[near_idx]
        ref_img_path = BASE_DIR / "data" / "reference" / "cifar10" / "images" / f"{ref_s['sample_id']}.png"
        if not ref_img_path.exists():
            ref_img_path = BASE_DIR / ref_s["file_path"]
        img = Image.open(ref_img_path)

        for trans_t in range(2):
            aug_img = apply_near_dup_transform(img, trans_t)
            sample_name = f"TEST_{seq_counter:05d}.png"
            dest_path = images_dir / sample_name
            aug_img.save(dest_path, format="PNG")

            with open(dest_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            samples_meta.append({
                "sample_id": f"TEST_{seq_counter:05d}",
                "file_path": f"images/{sample_name}",
                "submitted_label": ref_s["label_name"],
                "submitted_label_id": ref_s["label_id"],
                "reference_label": ref_s["label_name"],
                "reference_label_id": ref_s["label_id"],
                "sha256": file_hash,
                "is_manipulated": True,
                "manipulations": ["near_duplicate_augmentation"]
            })
            seq_counter += 1

    print("[3/4] Injected Wrong Labelling / Mismatched Labels (40 images)...")
    print("[4/4] Injected Synthetic Trigger Patches (30 images)...")

    # Create manifest.json
    manifest_data = {"samples": samples_meta}
    with open(OUTPUT_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # Create metadata.json
    metadata_data = {
        "contributor_id": "CUSTOM_RISKY_TEST",
        "dataset_name": "Risky_Test_Dataset_With_All_4_Errors",
        "source_dataset": "CIFAR-10 Controlled Test",
        "sample_count": len(samples_meta),
        "seed": 42,
        "manipulation_summary": {
            "exact_duplicate_flooding": "60 duplicate copies injected",
            "near_duplicates": "60 augmented near-duplicate copies injected",
            "wrong_labelling": "40 images with mismatched submitted labels",
            "controlled_trigger_patch": "30 images with synthetic magenta 6x6 patch"
        }
    }
    with open(OUTPUT_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata_data, f, indent=2)

    # Zip output dataset
    if ZIP_OUTPUT_PATH.exists():
        ZIP_OUTPUT_PATH.unlink()

    print(f"\nCompressing into {ZIP_OUTPUT_PATH.name}...")
    with zipfile.ZipFile(ZIP_OUTPUT_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                file_path = Path(root) / file
                archive_name = file_path.relative_to(OUTPUT_DIR)
                zipf.write(file_path, archive_name)

    print("=" * 70)
    print(f"  SUCCESSFULLY GENERATED: {ZIP_OUTPUT_PATH}")
    print(f"  Total Samples: {len(samples_meta)}")
    print(f"  File Size: {ZIP_OUTPUT_PATH.stat().st_size / 1024:.1f} KB")
    print("=" * 70)

if __name__ == "__main__":
    generate_risky_zip()

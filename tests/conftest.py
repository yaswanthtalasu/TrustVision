import os
import pytest
import tempfile
import json
import numpy as np
from pathlib import Path
from PIL import Image

from backend.config import CIFAR10_CLASSES


@pytest.fixture
def temp_environment(tmp_path):
    """
    Creates a lightweight synthetic reference dataset and contributor dataset for fast, isolated tests.
    """
    data_dir = tmp_path / "data"
    ref_dir = data_dir / "reference" / "cifar10"
    ref_images_dir = ref_dir / "images"
    ref_images_dir.mkdir(parents=True, exist_ok=True)

    contribs_dir = data_dir / "contributors"
    contribs_dir.mkdir(parents=True, exist_ok=True)

    generated_dir = data_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    # Generate 50 synthetic reference images (5 per class)
    ref_samples = []
    for i in range(50):
        cid = i % 10
        img_arr = np.random.randint(50, 200, (32, 32, 3), dtype=np.uint8)
        img = Image.fromarray(img_arr)
        img_path = ref_images_dir / f"REF_{i:05d}.png"
        img.save(img_path)

        ref_samples.append({
            "sample_id": f"REF_{i:05d}",
            "file_path": str(img_path.relative_to(tmp_path)),
            "label_id": cid,
            "label_name": CIFAR10_CLASSES[cid],
            "sha256": "dummy_hash_" + str(i)
        })

    ref_manifest = {
        "dataset": "CIFAR-10",
        "total_samples": 50,
        "classes": CIFAR10_CLASSES,
        "samples": ref_samples
    }

    with open(ref_dir / "reference_manifest.json", "w") as f:
        json.dump(ref_manifest, f)

    return {
        "root": tmp_path,
        "data_dir": data_dir,
        "ref_dir": ref_dir,
        "contribs_dir": contribs_dir,
        "generated_dir": generated_dir,
        "ref_manifest": ref_manifest
    }

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image
from backend.config import (
    BASE_DIR, TRIGGER_PATCH_SIZE, TRIGGER_PATCH_COLOR, TRIGGER_LOCATION
)
from backend.detectors.base import BaseDetector


class ControlledTriggerDetector(BaseDetector):
    def __init__(self):
        super().__init__(
            name="controlled_trigger",
            description="Detects controlled synthetic patch trigger patterns injected into image subsets for integrity validation."
        )
        self.target_color = np.array(TRIGGER_PATCH_COLOR, dtype=np.int32)
        self.patch_size = TRIGGER_PATCH_SIZE
        self.location = TRIGGER_LOCATION

    def analyze(self, contributor_id: str, contrib_dir: Path, ref_manifest: Dict[str, Any]) -> Dict[str, Any]:
        contrib_dir = Path(contrib_dir)
        manifest_file = contrib_dir / "manifest.json"

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        samples = manifest.get("samples", [])
        total_samples = len(samples)

        trigger_count = 0
        sample_evidence = []

        x, y = self.location
        pw, ph = self.patch_size, self.patch_size

        for s in samples:
            sid = s["sample_id"]
            img_path = BASE_DIR / s["file_path"]

            if not img_path.exists():
                continue

            img = Image.open(img_path).convert("RGB")
            arr = np.array(img)

            h, w, _ = arr.shape
            if x + pw <= w and y + ph <= h:
                patch_region = arr[y:y+ph, x:x+pw]
                # Calculate mean RGB color of patch region
                avg_color = np.mean(patch_region, axis=(0, 1))
                color_diff = np.linalg.norm(avg_color - self.target_color)

                # High pixel color uniformity check (synthetic patch is flat color)
                color_std = np.std(patch_region, axis=(0, 1))
                uniformity = np.mean(color_std)

                # Flag if color matches target magenta (255, 0, 255) with high uniformity
                if color_diff < 20.0 and uniformity < 5.0:
                    trigger_count += 1
                    confidence = round(1.0 - (color_diff / 255.0), 3)

                    sample_evidence.append({
                        "detector": self.name,
                        "contributor_id": contributor_id,
                        "sample_id": sid,
                        "evidence": {
                            "trigger_pattern": "synthetic_patch_6x6",
                            "location": f"({x},{y})",
                            "detected_color_rgb": [int(c) for c in avg_color],
                            "confidence_score": confidence
                        },
                        "severity": "CRITICAL",
                        "description": f"Controlled synthetic patch trigger detected at location ({x},{y}) with confidence {confidence}."
                    })

        affected_percentage = (trigger_count / total_samples * 100.0) if total_samples > 0 else 0.0

        return {
            "detector": self.name,
            "contributor_id": contributor_id,
            "total_samples": total_samples,
            "trigger_count": trigger_count,
            "affected_percentage": round(affected_percentage, 2),
            "patch_configuration": {
                "location": self.location,
                "patch_size": self.patch_size,
                "target_color": TRIGGER_PATCH_COLOR
            },
            "sample_evidence": sample_evidence
        }

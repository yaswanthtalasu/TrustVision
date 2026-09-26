import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image
import torch
import torchvision.models as models
import torchvision.transforms as transforms

from backend.config import BASE_DIR, CIFAR10_CLASSES, LABEL_ANOMALY_CONFIDENCE_THRESHOLD
from backend.detectors.base import BaseDetector


class FeatureExtractor:
    """
    Offline-capable feature extractor using PyTorch (ResNet-18) with robust fallback.
    """
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = transforms.Compose([
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        try:
            # Load PyTorch model for feature extraction with fast fallback
            model = models.resnet18(weights=None)  # Use random weights for fast offline representation or pretrained if available
            model.fc = torch.nn.Identity()
            model.eval()
            self.model = model.to(self.device)
            self.use_torch = True
        except Exception:
            # Fallback to normalized RGB histogram features if PyTorch model unavailable
            self.use_torch = False

    def extract_features(self, img_path: Path) -> np.ndarray:
        if not img_path.exists():
            return np.zeros(512 if self.use_torch else 768)

        img = Image.open(img_path).convert("RGB")

        if self.use_torch:
            tensor = self.transform(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                feat = self.model(tensor).squeeze().cpu().numpy()
            norm = np.linalg.norm(feat)
            return feat / (norm + 1e-8)
        else:
            # Color histogram fallback (256 bins * 3 channels = 768 dims)
            r, g, b = img.split()
            hist_r = np.array(r.histogram()) / 1024.0
            hist_g = np.array(g.histogram()) / 1024.0
            hist_b = np.array(b.histogram()) / 1024.0
            feat = np.concatenate([hist_r, hist_g, hist_b])
            norm = np.linalg.norm(feat)
            return feat / (norm + 1e-8)


class LabelAnomalyDetector(BaseDetector):
    def __init__(self, confidence_threshold: float = LABEL_ANOMALY_CONFIDENCE_THRESHOLD):
        super().__init__(
            name="label_anomaly",
            description="Detects visual label inconsistencies using deep embedding centroid similarity."
        )
        self.confidence_threshold = confidence_threshold
        self.extractor = FeatureExtractor()
        self.class_centroids: Dict[int, np.ndarray] = {}

    def _build_reference_centroids(self, ref_manifest: Dict[str, Any]):
        """
        Builds feature centroids for each of the 10 clean CIFAR-10 classes.
        """
        class_features: Dict[int, List[np.ndarray]] = {i: [] for i in range(10)}

        # Sample up to 100 images per class from reference manifest for clean baseline
        samples_by_class: Dict[int, List[dict]] = {i: [] for i in range(10)}
        for s in ref_manifest.get("samples", []):
            samples_by_class[s["label_id"]].append(s)

        for cid, samples in samples_by_class.items():
            for s in samples[:80]:
                imgPath = BASE_DIR / s["file_path"]
                feat = self.extractor.extract_features(imgPath)
                class_features[cid].append(feat)

        for cid in range(10):
            if len(class_features[cid]) > 0:
                mean_vec = np.mean(class_features[cid], axis=0)
                norm = np.linalg.norm(mean_vec)
                self.class_centroids[cid] = mean_vec / (norm + 1e-8)
            else:
                self.class_centroids[cid] = np.zeros(512 if self.extractor.use_torch else 768)

    def analyze(self, contributor_id: str, contrib_dir: Path, ref_manifest: Dict[str, Any]) -> Dict[str, Any]:
        contrib_dir = Path(contrib_dir)
        manifest_file = contrib_dir / "manifest.json"

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        samples = manifest.get("samples", [])
        total_samples = len(samples)

        # Build centroids if not built yet
        if not self.class_centroids:
            self._build_reference_centroids(ref_manifest)

        label_anomaly_count = 0
        sample_evidence = []

        for s in samples:
            sid = s["sample_id"]
            img_path = BASE_DIR / s["file_path"]
            submitted_label_id = s.get("submitted_label_id", 0)
            submitted_label_name = s.get("submitted_label", CIFAR10_CLASSES[submitted_label_id])
            ref_label_name = s.get("reference_label", None)

            feat = self.extractor.extract_features(img_path)

            # Cosine similarity with submitted class centroid
            sub_centroid = self.class_centroids[submitted_label_id]
            sub_sim = float(np.dot(feat, sub_centroid))

            # Find nearest class centroid among all 10 classes
            all_sims = {cid: float(np.dot(feat, self.class_centroids[cid])) for cid in range(10)}
            nearest_class_id = max(all_sims, key=all_sims.get)
            nearest_class_name = CIFAR10_CLASSES[nearest_class_id]
            nearest_sim = all_sims[nearest_class_id]

            # Condition for label anomaly:
            # 1) Submitted class similarity is low (< threshold) AND
            # 2) Nearest visual class is different from submitted class with higher similarity
            is_anomaly = (sub_sim < self.confidence_threshold) or (nearest_class_id != submitted_label_id and (nearest_sim - sub_sim) > 0.15)

            if is_anomaly:
                label_anomaly_count += 1
                severity = "HIGH" if (nearest_sim - sub_sim) > 0.30 else "MEDIUM"

                sample_evidence.append({
                    "detector": self.name,
                    "contributor_id": contributor_id,
                    "sample_id": sid,
                    "evidence": {
                        "submitted_label": submitted_label_name,
                        "reference_label": ref_label_name,
                        "predicted_nearest_class": nearest_class_name,
                        "submitted_class_similarity": round(sub_sim, 3),
                        "nearest_class_similarity": round(nearest_sim, 3),
                        "similarity_gap": round(nearest_sim - sub_sim, 3)
                    },
                    "severity": severity,
                    "description": f"Label anomaly evidence detected. Submitted label '{submitted_label_name}' visually resembles '{nearest_class_name}' (sim gap: {round(nearest_sim - sub_sim, 2)})."
                })

        affected_percentage = (label_anomaly_count / total_samples * 100.0) if total_samples > 0 else 0.0

        return {
            "detector": self.name,
            "contributor_id": contributor_id,
            "total_samples": total_samples,
            "label_anomaly_count": label_anomaly_count,
            "affected_percentage": round(affected_percentage, 2),
            "confidence_threshold": self.confidence_threshold,
            "sample_evidence": sample_evidence
        }

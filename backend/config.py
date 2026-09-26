import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REFERENCE_DIR = DATA_DIR / "reference" / "cifar10"
CONTRIBUTORS_DIR = DATA_DIR / "contributors"
GENERATED_DIR = DATA_DIR / "generated"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = GENERATED_DIR / "reports"
EVIDENCE_DIR = GENERATED_DIR / "evidence"
MANIFESTS_DIR = GENERATED_DIR / "manifests"

# Ensure essential directories exist
for directory in [DATA_DIR, REFERENCE_DIR, CONTRIBUTORS_DIR, GENERATED_DIR, MODELS_DIR, REPORTS_DIR, EVIDENCE_DIR, MANIFESTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# CIFAR-10 metadata
CIFAR10_CLASSES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck"
]
NUM_CLASSES = len(CIFAR10_CLASSES)

# Contributor Generation Defaults
DEFAULT_SEED = 42
DEFAULT_SAMPLES_PER_CONTRIBUTOR = 2000  # Lightweight, scalable sample size for fast execution

# Contributor IDs
CONTRIBUTOR_IDS = ["C1", "C2", "C3", "C4"]

# Detector Configurations
EXACT_DUP_SEVERITY_THRESHOLD = 0.02  # >2% duplicates triggers warning

NEAR_DUP_PHASH_THRESHOLD = 8  # Hamming distance <= 8 considered near duplicate
NEAR_DUP_COSINE_THRESHOLD = 0.90 # Cosine similarity >= 0.90 considered near duplicate

LABEL_ANOMALY_CONFIDENCE_THRESHOLD = 0.35 # Low feature similarity to class centroid

TRIGGER_PATCH_SIZE = 6  # 6x6 pixels
TRIGGER_PATCH_COLOR = (255, 0, 255) # Magenta synthetic trigger patch
TRIGGER_LOCATION = (2, 2)  # Top-left offset

DISTRIBUTION_CHI_SQUARE_P_VAL = 0.01  # p-value threshold for distribution shift

# Decision Thresholds for Aggregator
# Risk score calculation weights
SCORE_EXACT_DUP_WEIGHT = 20.0
SCORE_NEAR_DUP_WEIGHT = 15.0
SCORE_LABEL_ANOMALY_WEIGHT = 35.0
SCORE_TRIGGER_WEIGHT = 40.0
SCORE_DISTRIBUTION_WEIGHT = 15.0

QUARANTINE_SCORE_THRESHOLD = 30.0
REVIEW_SCORE_THRESHOLD = 10.0

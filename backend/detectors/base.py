from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class BaseDetector(ABC):
    """
    Abstract Base Class for all TrustVision Data Integrity Detectors.
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def analyze(self, contributor_id: str, contrib_dir: Path, ref_manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes detector logic on a contributor dataset and produces sample & aggregated evidence.
        """
        pass

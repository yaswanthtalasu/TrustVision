import os
from pathlib import Path
import hashlib
import torch
import torch.nn as nn

def generate_demos():
    BASE_DIR = Path(__file__).resolve().parent.parent
    DEMO_DIR = BASE_DIR / "demo"
    CLEAN_DIR = DEMO_DIR / "clean"
    TAMPERED_DIR = DEMO_DIR / "tampered"
    
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    TAMPERED_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Create a simple dummy model
    class DummyModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(10, 2)
            
    model = DummyModel()
    clean_model_path = CLEAN_DIR / "company_model.pth"
    torch.save(model.state_dict(), clean_model_path)
    
    # 2. Calculate its SHA-256
    sha256 = hashlib.sha256()
    with open(clean_model_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            
    clean_hash = sha256.hexdigest().lower()
    
    clean_hash_path = CLEAN_DIR / "company_model.sha256"
    with open(clean_hash_path, "w") as f:
        f.write(clean_hash + "  company_model.pth")
        
    print(f"Clean demo generated at {CLEAN_DIR}")
    print(f"Original Hash: {clean_hash}")
    
    # 3. Create tampered model (modify slightly)
    model.linear.bias.data += 0.01
    tampered_model_path = TAMPERED_DIR / "company_model.pth"
    torch.save(model.state_dict(), tampered_model_path)
    
    # 4. Copy the original hash file to tampered directory (to simulate mismatch)
    tampered_hash_path = TAMPERED_DIR / "company_model.sha256"
    with open(tampered_hash_path, "w") as f:
        f.write(clean_hash + "  company_model.pth")
        
    print(f"Tampered demo generated at {TAMPERED_DIR}")
    
if __name__ == "__main__":
    generate_demos()

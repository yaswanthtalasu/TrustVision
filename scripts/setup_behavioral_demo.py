import os
from pathlib import Path
import hashlib
import torch
from torchvision.models import resnet18

def setup_demo():
    BASE_DIR = Path(__file__).resolve().parent.parent
    DEMO_DIR = BASE_DIR / "demo"
    CLEAN_DIR = DEMO_DIR / "clean"
    MODIFIED_DIR = DEMO_DIR / "tampered"
    
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    MODIFIED_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Generating Trusted Reference / Clean Company Model (ResNet-18)...")
    # 1. Create a ResNet-18 model
    model = resnet18(num_classes=10)
    
    # We will use this as the reference and the clean model
    clean_model_path = CLEAN_DIR / "company_model.pth"
    torch.save(model.state_dict(), clean_model_path)
    
    # Calculate SHA-256
    sha256 = hashlib.sha256()
    with open(clean_model_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
            
    clean_hash = sha256.hexdigest().lower()
    
    with open(CLEAN_DIR / "company_model.sha256", "w") as f:
        f.write(clean_hash + "  company_model.pth")
        
    print(f"Clean demo generated at {CLEAN_DIR}")
    print(f"Original Hash: {clean_hash}")
    
    print("Generating Controlled Modified Company Model...")
    # 3. Create modified model (modify the fully connected layer slightly)
    # We change weights in a way that affects predictions.
    with torch.no_grad():
        model.fc.weight.data += 5.0  # Large perturbation to force behavioral deviation
        model.fc.bias.data += 5.0
        
    modified_model_path = MODIFIED_DIR / "company_model.pth"
    torch.save(model.state_dict(), modified_model_path)
    
    # 4. Copy the original hash file to modified directory
    with open(MODIFIED_DIR / "company_model.sha256", "w") as f:
        f.write(clean_hash + "  company_model.pth")
        
    print(f"Modified demo generated at {MODIFIED_DIR}")
    
if __name__ == "__main__":
    setup_demo()

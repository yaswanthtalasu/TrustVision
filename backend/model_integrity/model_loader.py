import torch
import torch.nn as nn
from torchvision.models import resnet18

def load_resnet18_model(model_path):
    model = resnet18(num_classes=10)
    # Ensure offline processing on CPU
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model

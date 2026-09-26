import pytest
import torch
import tempfile
from pathlib import Path
from torchvision.models import resnet18
from backend.model_integrity.behavioral_analyzer import BehavioralAnalyzer
from backend.model_integrity.test_generator import generate_test_suites
from backend.model_integrity.model_loader import load_resnet18_model

@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

def test_behavioral_clean(temp_workspace):
    model = resnet18(num_classes=10)
    model_path = temp_workspace / "model.pth"
    torch.save(model.state_dict(), model_path)
    
    ref_model = load_resnet18_model(model_path)
    sub_model = load_resnet18_model(model_path)
    
    normal_inputs, trigger_inputs = generate_test_suites(num_samples=10)
    
    analyzer = BehavioralAnalyzer(ref_model, sub_model)
    result = analyzer.analyze(normal_inputs, trigger_inputs)
    
    assert result["status"] == "PASS"
    assert result["normal_test"]["agreement"] == 1.0
    assert result["trigger_test"]["deviation_rate"] == 0.0

def test_behavioral_modified(temp_workspace):
    ref_model = resnet18(num_classes=10)
    ref_path = temp_workspace / "ref_model.pth"
    torch.save(ref_model.state_dict(), ref_path)
    
    sub_model = resnet18(num_classes=10)
    with torch.no_grad():
        sub_model.fc.weight.data += 10.0
    sub_path = temp_workspace / "sub_model.pth"
    torch.save(sub_model.state_dict(), sub_path)
    
    ref_loaded = load_resnet18_model(ref_path)
    sub_loaded = load_resnet18_model(sub_path)
    
    normal_inputs, trigger_inputs = generate_test_suites(num_samples=10)
    
    analyzer = BehavioralAnalyzer(ref_loaded, sub_loaded)
    result = analyzer.analyze(normal_inputs, trigger_inputs)
    
    assert result["status"] == "REVIEW"
    assert result["normal_test"]["agreement"] < 1.0 or result["trigger_test"]["deviation_rate"] > 0.0

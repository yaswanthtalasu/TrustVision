import pytest
import os
from pathlib import Path
from backend.inference_integrity.engine import run_inference, verify_record

import torch
from torchvision.models import resnet18
from PIL import Image

@pytest.fixture
def dummy_files(tmp_path):
    img_path1 = tmp_path / "test_img1.jpg"
    img1 = Image.new('RGB', (32, 32), color = 'red')
    img1.save(img_path1)
    
    img_path2 = tmp_path / "test_img2.jpg"
    img2 = Image.new('RGB', (32, 32), color = 'blue')
    img2.save(img_path2)
    
    model_path = tmp_path / "test_model.pth"
    model = resnet18(num_classes=10)
    torch.save(model.state_dict(), model_path)
    
    return img_path1, img_path2, model_path

def test_valid_record(dummy_files):
    img_path1, img_path2, model_path = dummy_files
    record = run_inference(img_path1, model_path, "TestModel")
    result = verify_record(record.dict(), check_replay=False)
    assert result.status == "VALID"

def test_different_images(dummy_files):
    img_path1, img_path2, model_path = dummy_files
    record1 = run_inference(img_path1, model_path, "TestModel")
    record2 = run_inference(img_path2, model_path, "TestModel")
    
    assert record1.input_hash != record2.input_hash
    assert record1.record_hash != record2.record_hash

def test_tamper_prediction(dummy_files):
    img_path1, img_path2, model_path = dummy_files
    record = run_inference(img_path1, model_path, "TestModel")
    record_dict = record.dict()
    record_dict["prediction"] = "HACKED"
    
    result = verify_record(record_dict, check_replay=False)
    assert result.status == "TAMPERING DETECTED"
    assert result.checks["signature"] == "FAIL"

def test_tamper_confidence(dummy_files):
    img_path1, img_path2, model_path = dummy_files
    record = run_inference(img_path1, model_path, "TestModel")
    record_dict = record.dict()
    record_dict["confidence"] = 0.99
    
    result = verify_record(record_dict, check_replay=False)
    assert result.status == "TAMPERING DETECTED"
    assert result.checks["signature"] == "FAIL"

def test_replay_detection(dummy_files):
    img_path1, img_path2, model_path = dummy_files
    record = run_inference(img_path1, model_path, "TestModel")
    
    # First verification without replay check
    result = verify_record(record.dict(), check_replay=False)
    assert result.status == "VALID"
    
    # Second submission (Replay)
    result_replay = verify_record(record.dict(), check_replay=True)
    assert result_replay.status == "REPLAY DETECTED"
    assert result_replay.checks["replay"] == "FAIL"

def test_tamper_input_hash(dummy_files):
    img_path1, img_path2, model_path = dummy_files
    record = run_inference(img_path1, model_path, "TestModel")
    record_dict = record.dict()
    record_dict["input_hash"] = "fakehash123"
    
    result = verify_record(record_dict, check_replay=False)
    assert result.status == "TAMPERING DETECTED"
    assert result.checks["signature"] == "FAIL"

def test_tamper_model_hash(dummy_files):
    img_path1, img_path2, model_path = dummy_files
    record = run_inference(img_path1, model_path, "TestModel")
    record_dict = record.dict()
    record_dict["model_hash"] = "fakehash123"
    
    result = verify_record(record_dict, check_replay=False)
    assert result.status == "TAMPERING DETECTED"
    assert result.checks["signature"] == "FAIL"

def test_tamper_hash_chain(dummy_files):
    img_path1, img_path2, model_path = dummy_files
    # Run twice to get a previous_record_hash
    run_inference(img_path1, model_path, "TestModel")
    record = run_inference(img_path2, model_path, "TestModel")
    record_dict = record.dict()
    
    # Tamper with the chain
    record_dict["previous_record_hash"] = "fake_chain_hash"
    
    result = verify_record(record_dict, check_replay=False)
    assert result.status == "TAMPERING DETECTED"
    assert result.checks["signature"] == "FAIL"

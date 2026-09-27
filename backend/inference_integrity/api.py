from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from pathlib import Path
import shutil
import json
from backend.config import BASE_DIR
from backend.inference_integrity.engine import run_inference, verify_record
from backend.inference_integrity.schemas import InferenceRecord

router = APIRouter(prefix='/api/inference', tags=['Inference Integrity'])
UPLOAD_DIR = BASE_DIR / 'uploads' / 'inference'

@router.post('/run')
async def api_run_inference(image: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_path = UPLOAD_DIR / image.filename
    with open(image_path, 'wb') as f:
        shutil.copyfileobj(image.file, f)
        
    model_path = BASE_DIR / 'demo' / 'clean' / 'company_model.pth'
    if not model_path.exists():
        raise HTTPException(status_code=500, detail="Approved model company_model.pth not found. Please run setup_behavioral_demo.py first.")
        
    record = run_inference(image_path, model_path, 'ResNet18-Clean')
    return record

@router.post('/verify')
async def api_verify(record: dict):
    result = verify_record(record, check_replay=False)
    return result

@router.post('/replay-test')
async def api_replay_test(record: dict):
    result = verify_record(record, check_replay=True)
    return result

@router.post('/tamper-test')
async def api_tamper_test(record: dict):
    # Tamper the prediction
    record['prediction'] = 'Dog' if record.get('prediction') == 'Cat' else 'Cat'
    result = verify_record(record, check_replay=False)
    return result

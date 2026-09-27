import json
from pathlib import Path
from backend.config import BASE_DIR
from backend.inference_integrity.schemas import InferenceRecord

STORE_FILE = BASE_DIR / 'data' / 'inference_records.json'

def load_records():
    if not STORE_FILE.exists():
        return []
    with open(STORE_FILE, 'r') as f:
        return [InferenceRecord(**r) for r in json.load(f)]

def save_records(records):
    STORE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE_FILE, 'w') as f:
        json.dump([r.dict() for r in records], f, indent=2)

def append_record(record: InferenceRecord):
    records = load_records()
    records.append(record)
    save_records(records)

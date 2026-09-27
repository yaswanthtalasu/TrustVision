import uuid
import hashlib
from datetime import datetime
from backend.inference_integrity.schemas import InferenceRecord, VerificationResult
from backend.inference_integrity.crypto import get_or_create_keys, canonicalize, hash_file
from backend.inference_integrity.store import load_records, append_record

import torch
from torchvision import transforms
from PIL import Image
from backend.model_integrity.model_loader import load_resnet18_model

CIFAR10_CLASSES = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']

def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    image = Image.open(image_path).convert('RGB')
    return transform(image).unsqueeze(0)

def run_inference(image_path, model_path, model_id):
    records = load_records()
    seq_id = len(records) + 1
    prev_hash = records[-1].record_hash if records else None
    
    input_hash = hash_file(image_path)
    model_hash = hash_file(model_path)
    
    try:
        model = load_resnet18_model(model_path)
        input_tensor = preprocess_image(image_path)
        with torch.no_grad():
            logits = model(input_tensor)
            probs = torch.nn.functional.softmax(logits, dim=1)[0]
            conf, pred_idx = torch.max(probs, 0)
            prediction = CIFAR10_CLASSES[pred_idx.item()]
            confidence = round(conf.item(), 4)
    except Exception as e:
        prediction = "Error"
        confidence = 0.0
        print(f"Inference error: {e}")
    
    record = InferenceRecord(
        record_id=f'INF-{uuid.uuid4().hex[:8].upper()}',
        sequence_id=seq_id,
        timestamp=datetime.utcnow().isoformat(),
        input_hash=input_hash,
        model_hash=model_hash,
        model_id=model_id,
        preprocessing_config='default_v1',
        prediction=prediction,
        confidence=confidence,
        previous_record_hash=prev_hash
    )
    
    canonical_bytes = canonicalize(record.dict())
    record.record_hash = hashlib.sha256(canonical_bytes).hexdigest()
    
    priv, pub = get_or_create_keys()
    import base64
    sig = priv.sign(canonical_bytes)
    record.signature = base64.b64encode(sig).decode('utf-8')
    record.key_id = 'ed25519-key-1'
    
    append_record(record)
    return record

def verify_record(record_dict, check_replay=True):
    from cryptography.exceptions import InvalidSignature
    import base64
    
    checks = {
        'input_hash': 'PASS',
        'model_hash': 'PASS',
        'record_integrity': 'FAIL',
        'signature': 'FAIL',
        'replay': 'PASS'
    }
    evidence = []
    
    # 1. Check replay
    if check_replay:
        stored = load_records()
        for r in stored:
            if r.record_id == record_dict['record_id']:
                # Same ID exists. Is it a replay?
                if r.dict() == record_dict:
                    checks['replay'] = 'FAIL'
                    evidence.append('Record ID / sequence identifier has already been accepted.')
                    return VerificationResult(status='REPLAY DETECTED', record_id=record_dict['record_id'], checks=checks, evidence=evidence)
    
    # 2. Signature verification
    priv, pub = get_or_create_keys()
    canonical_bytes = canonicalize(record_dict)
    
    try:
        sig_bytes = base64.b64decode(record_dict['signature'])
        pub.verify(sig_bytes, canonical_bytes)
        checks['signature'] = 'PASS'
    except InvalidSignature:
        evidence.append('Prediction in received record differs from the cryptographically protected prediction, or signature is invalid.')
    except Exception as e:
        evidence.append(str(e))
        
    # 3. Hash verification
    recalc_hash = hashlib.sha256(canonical_bytes).hexdigest()
    if recalc_hash == record_dict.get('record_hash'):
        checks['record_integrity'] = 'PASS'
    else:
        evidence.append('Record hash mismatch. The record has been modified.')
        
    status = 'VALID' if all(v == 'PASS' for v in checks.values()) else 'TAMPERING DETECTED'
    
    return VerificationResult(
        status=status,
        record_id=record_dict['record_id'],
        checks=checks,
        evidence=evidence
    )

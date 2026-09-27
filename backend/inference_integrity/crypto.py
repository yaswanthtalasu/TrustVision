import json
import hashlib
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from pathlib import Path
from backend.config import BASE_DIR

KEYS_DIR = BASE_DIR / 'data' / 'keys'

def get_or_create_keys():
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    priv_path = KEYS_DIR / 'inference_ed25519.priv'
    pub_path = KEYS_DIR / 'inference_ed25519.pub'
    
    if priv_path.exists() and pub_path.exists():
        with open(priv_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(pub_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(f.read())
        return private_key, public_key

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    with open(priv_path, 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(pub_path, 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    return private_key, public_key

def canonicalize(record_dict):
    canonical_dict = {
        'record_id': record_dict['record_id'],
        'sequence_id': record_dict['sequence_id'],
        'timestamp': record_dict['timestamp'],
        'input_hash': record_dict['input_hash'],
        'model_hash': record_dict['model_hash'],
        'model_id': record_dict['model_id'],
        'preprocessing_config': record_dict['preprocessing_config'],
        'prediction': record_dict['prediction'],
        'confidence': float(record_dict['confidence'])
    }
    if record_dict.get('previous_record_hash'):
        canonical_dict['previous_record_hash'] = record_dict['previous_record_hash']
    return json.dumps(canonical_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')

def hash_file(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest().lower()

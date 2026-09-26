def calculate_sha256(file_path, chunk_size=8192):
    import hashlib
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest().lower()

def parse_sha256_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    
    # Extract the first 64 hexadecimal characters
    import re
    match = re.search(r'[a-fA-F0-9]{64}', content)
    if match:
        return match.group(0).lower()
    return None

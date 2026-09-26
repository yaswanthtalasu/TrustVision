import urllib.request
import os
from pathlib import Path
import tarfile

URL = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
DEST_DIR = Path("data/reference/cifar10/raw")

def download_cifar10():
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    tar_path = DEST_DIR / "cifar-10-python.tar.gz"
    
    if tar_path.exists():
        print(f"Archive already exists at {tar_path}")
        return

    print(f"Downloading CIFAR-10 archive from {URL} to {tar_path}...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(tar_path, "wb") as out_file:
        length = response.getheader("Content-Length")
        total_size = int(length) if length else 0
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        while True:
            buffer = response.read(chunk_size)
            if not buffer:
                break
            downloaded += len(buffer)
            out_file.write(buffer)
            if total_size > 0:
                pct = (downloaded / total_size) * 100
                print(f"  Downloaded {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({pct:.1f}%)", end="\r")
    
    print("\nDownload finished! Extracting archive...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=DEST_DIR)
    print("CIFAR-10 extracted successfully.")

if __name__ == "__main__":
    download_cifar10()

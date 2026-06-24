import kagglehub
import shutil
import os
from dotenv import load_dotenv

load_dotenv()  # loads KAGGLE_USERNAME and KAGGLE_KEY from .env

DATASET = "olistbr/brazilian-ecommerce"
DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

print(f"Downloading dataset: {DATASET}...")
path = kagglehub.dataset_download(DATASET)
print(f"Downloaded to cache: {path}")

copied = []
for filename in os.listdir(path):
    if filename.endswith(".csv"):
        src = os.path.join(path, filename)
        dst = os.path.join(DATA_DIR, filename)
        shutil.copy(src, dst)
        copied.append(filename)
        print(f"  Copied: {filename}")

print(f"\nDone. {len(copied)} CSV files in ./{DATA_DIR}/")
for f in sorted(copied):
    size_kb = os.path.getsize(os.path.join(DATA_DIR, f)) // 1024
    print(f"  {f} ({size_kb} KB)")

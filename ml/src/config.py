from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"          # put Normal/ and stone/ folders here
SPLIT_DIR = ROOT / "data" / "splits"     # created by prepare_data.py
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"

IMG_SIZE = 224
# Order matters: index 0 = Normal, index 1 = stone. Sigmoid output = P(stone).
CLASS_NAMES = ["Normal", "stone"]
SEED = 42
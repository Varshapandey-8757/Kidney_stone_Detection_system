"""Clean raw dataset, remove duplicates, preprocess, split 70/15/15.

Usage:  python src/prepare_data.py --raw data/raw
Expected raw layout:  raw/Normal/*.jpg  and  raw/stone/*.jpg  (case-insensitive names)
"""
import argparse
import hashlib
import shutil
from pathlib import Path

import cv2
from sklearn.model_selection import train_test_split

from config import CLASS_NAMES, RAW_DIR, SEED, SPLIT_DIR
from preprocess import preprocess_gray

EXT = {".jpg", ".jpeg", ".png", ".bmp"}


def find_class_dir(raw: Path, name: str) -> Path:
    matches = sorted(
        d for d in raw.rglob("*")
        if d.is_dir() and d.name.casefold() == name.casefold()
    )
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(
            f"Found multiple '{name}' folders inside {raw}; pass the directory "
            "that contains exactly one folder for each class."
        )
    raise SystemExit(f"Folder '{name}' not found inside {raw}")


def main(raw: Path):
    seen = {}            # pixel-hash -> class name
    items = []           # (class_name, processed_image)
    stats = {c: {"read": 0, "bad": 0, "dup": 0} for c in CLASS_NAMES}

    for cname in CLASS_NAMES:
        cdir = find_class_dir(raw, cname)
        for p in sorted(cdir.rglob("*")):
            if p.suffix.lower() not in EXT:
                continue
            stats[cname]["read"] += 1
            gray = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if gray is None:
                stats[cname]["bad"] += 1
                continue
            proc = preprocess_gray(gray)
            h = hashlib.md5(proc.tobytes()).hexdigest()
            if h in seen:
                stats[cname]["dup"] += 1
                if seen[h] != cname:
                    print(f"WARNING: same image in both classes: {p.name}")
                continue
            seen[h] = cname
            items.append((cname, proc))

    print("Read/bad/duplicate counts:", stats)
    labels = [c for c, _ in items]
    idx = list(range(len(items)))
    tr, rest = train_test_split(idx, test_size=0.30, stratify=labels, random_state=SEED)
    va, te = train_test_split(rest, test_size=0.50, stratify=[labels[i] for i in rest], random_state=SEED)

    if SPLIT_DIR.exists():
        shutil.rmtree(SPLIT_DIR)
    for split, ids in (("train", tr), ("val", va), ("test", te)):
        for c in CLASS_NAMES:
            (SPLIT_DIR / split / c).mkdir(parents=True, exist_ok=True)
        for n, i in enumerate(ids):
            c, img = items[i]
            cv2.imwrite(str(SPLIT_DIR / split / c / f"{n:05d}.png"), img)
        counts = {c: sum(1 for i in ids if items[i][0] == c) for c in CLASS_NAMES}
        print(f"{split}: {len(ids)} images {counts}")
    print("NOTE: dataset has no patient IDs, so split is by image (state this limitation in the paper).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=RAW_DIR)
    main(ap.parse_args().raw)
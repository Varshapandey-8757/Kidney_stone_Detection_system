"""Evaluate on the untouched test split.  python src/evaluate.py [--model path]"""
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (ConfusionMatrixDisplay, classification_report, confusion_matrix,
                             roc_auc_score, roc_curve)

from config import CLASS_NAMES, IMG_SIZE, MODEL_DIR, REPORT_DIR, SPLIT_DIR


def main(path, thr):
    model = tf.keras.models.load_model(path, compile=False)
    ds = tf.keras.utils.image_dataset_from_directory(
        SPLIT_DIR / "test", label_mode="binary", class_names=CLASS_NAMES, color_mode="rgb",
        image_size=(IMG_SIZE, IMG_SIZE), batch_size=32, shuffle=False)
    y_true = np.concatenate([y.numpy().ravel() for _, y in ds]).astype(int)
    y_prob = model.predict(ds).ravel()
    y_pred = (y_prob >= thr).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    metrics = {
        "accuracy": float((tp + tn) / len(y_true)),
        "precision": float(tp / max(tp + fp, 1)),
        "recall_sensitivity": float(tp / max(tp + fn, 1)),
        "specificity": float(tn / max(tn + fp, 1)),
        "f1": float(2 * tp / max(2 * tp + fp + fn, 1)),
        "auc": float(roc_auc_score(y_true, y_prob)),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "threshold": thr,
    }
    print(classification_report(y_true, y_pred, target_names=CLASS_NAMES))
    print(json.dumps(metrics, indent=2))

    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    ConfusionMatrixDisplay(confusion_matrix(y_true, y_pred), display_labels=CLASS_NAMES).plot()
    plt.savefig(REPORT_DIR / "confusion_matrix.png", dpi=150); plt.close()
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    plt.plot(fpr, tpr, label=f"AUC={metrics['auc']:.3f}"); plt.plot([0, 1], [0, 1], "--")
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate"); plt.legend()
    plt.savefig(REPORT_DIR / "roc_curve.png", dpi=150)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=str(MODEL_DIR / "kidney_model.keras"))
    ap.add_argument("--threshold", type=float, default=0.5)
    a = ap.parse_args()
    main(a.model, a.threshold)
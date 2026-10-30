"""Train the classifier.

python src/train.py --model mobilenet --epochs 12 --ft-epochs 8
python src/train.py --model cnn --epochs 25          (baseline for comparison table)
"""
import argparse
import json
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow import keras

from config import CLASS_NAMES, IMG_SIZE, MODEL_DIR, REPORT_DIR, SEED, SPLIT_DIR
from model import build_cnn, build_mobilenet, compile_model


def load(split, batch, shuffle):
    return tf.keras.utils.image_dataset_from_directory(
        SPLIT_DIR / split, labels="inferred", label_mode="binary", class_names=CLASS_NAMES,
        color_mode="rgb", image_size=(IMG_SIZE, IMG_SIZE), batch_size=batch,
        shuffle=shuffle, seed=SEED,
    ).prefetch(tf.data.AUTOTUNE)


def class_weights(ds):
    y = np.concatenate([b.numpy().ravel() for _, b in ds])
    n, n1 = len(y), y.sum()
    return {0: n / (2 * (n - n1)), 1: n / (2 * n1)}


def callbacks():
    return [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.3, patience=2, min_lr=1e-7),
    ]


def plot_history(histories, name):
    REPORT_DIR.mkdir(exist_ok=True)
    acc = sum([h.history["accuracy"] for h in histories], [])
    vacc = sum([h.history["val_accuracy"] for h in histories], [])
    loss = sum([h.history["loss"] for h in histories], [])
    vloss = sum([h.history["val_loss"] for h in histories], [])
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(acc, label="train"); ax[0].plot(vacc, label="val"); ax[0].set_title("Accuracy"); ax[0].legend()
    ax[1].plot(loss, label="train"); ax[1].plot(vloss, label="val"); ax[1].set_title("Loss"); ax[1].legend()
    fig.tight_layout(); fig.savefig(REPORT_DIR / f"training_curves_{name}.png", dpi=150)


def main(a):
    tf.keras.utils.set_random_seed(SEED)
    train, val = load("train", a.batch, True), load("val", a.batch, False)
    cw = class_weights(train)
    print("class weights:", cw)

    model, base = build_mobilenet() if a.model == "mobilenet" else build_cnn()
    compile_model(model, 1e-3)
    h1 = model.fit(train, validation_data=val, epochs=a.epochs, class_weight=cw, callbacks=callbacks())
    histories = [h1]

    if a.model == "mobilenet" and a.ft_epochs > 0:
        base.trainable = True
        for layer in base.layers[:-30]:
            layer.trainable = False
        for layer in base.layers:
            if isinstance(layer, keras.layers.BatchNormalization):
                layer.trainable = False
        compile_model(model, 1e-5)
        h2 = model.fit(train, validation_data=val, epochs=a.ft_epochs, class_weight=cw, callbacks=callbacks())
        histories.append(h2)

    MODEL_DIR.mkdir(exist_ok=True)
    out = MODEL_DIR / ("kidney_model.keras" if a.model == "mobilenet" else "kidney_cnn_baseline.keras")
    model.save(out)
    if a.model == "mobilenet":
        (MODEL_DIR / "model_info.json").write_text(json.dumps({
            "version": f"mobilenetv2-{datetime.now():%Y%m%d}",
            "threshold": 0.5, "class_names": CLASS_NAMES, "img_size": IMG_SIZE,
        }, indent=2))
    plot_history(histories, a.model)
    print("saved:", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["mobilenet", "cnn"], default="mobilenet")
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--ft-epochs", type=int, default=8)
    ap.add_argument("--batch", type=int, default=32)
    main(ap.parse_args())
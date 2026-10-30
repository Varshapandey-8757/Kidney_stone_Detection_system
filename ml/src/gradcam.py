"""Grad-CAM overlays for a few test images:  python src/gradcam.py --n 8"""
import argparse

import cv2
import numpy as np
import tensorflow as tf

from config import CLASS_NAMES, MODEL_DIR, REPORT_DIR, SPLIT_DIR
from preprocess import to_model_input


def heatmap(model, img224_gray):
    x = tf.convert_to_tensor(to_model_input(img224_gray)[None] / 127.5 - 1.0)
    names = [l.name for l in model.layers]
    backbone = model.get_layer("backbone")
    head = model.layers[names.index("backbone") + 1:]
    with tf.GradientTape() as tape:
        conv = backbone(x, training=False)
        tape.watch(conv)
        h = conv
        for layer in head:
            h = layer(h, training=False)
        score = h[:, 0]
    grads = tape.gradient(score, conv)
    w = tf.reduce_mean(grads, axis=(1, 2))[0]
    cam = tf.nn.relu(tf.reduce_sum(conv[0] * w, axis=-1)).numpy()
    cam /= cam.max() + 1e-8
    return cam, float(score.numpy()[0])


def overlay(gray224, cam):
    heat = cv2.applyColorMap(np.uint8(255 * cv2.resize(cam, gray224.shape[::-1])), cv2.COLORMAP_JET)
    return cv2.addWeighted(cv2.cvtColor(gray224, cv2.COLOR_GRAY2BGR), 0.6, heat, 0.4, 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    n = ap.parse_args().n
    model = tf.keras.models.load_model(MODEL_DIR / "kidney_model.keras", compile=False)
    out = REPORT_DIR / "gradcam"; out.mkdir(parents=True, exist_ok=True)
    for c in CLASS_NAMES:
        for p in sorted((SPLIT_DIR / "test" / c).glob("*.png"))[:n]:
            g = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            cam, prob = heatmap(model, g)
            cv2.imwrite(str(out / f"{c}_{p.stem}_p{prob:.2f}.png"), overlay(g, cam))
    print("saved to", out)
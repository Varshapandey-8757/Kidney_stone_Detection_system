import json
import threading
from pathlib import Path

import cv2
import numpy as np

from app.services.preprocess import preprocess_gray, to_model_input


class ModelNotReady(RuntimeError):
    pass


class MLService:
    def __init__(self):
        self.model = None
        self.version = "unversioned"
        self.threshold = 0.5
        self._lock = threading.Lock()

    @property
    def ready(self) -> bool:
        return self.model is not None

    def load(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            raise ModelNotReady(f"Model file not found: {p}")
        import tensorflow as tf  # lazy: keeps the API importable without TF (tests)
        from tensorflow import keras

        self._tf = tf
        self.model = keras.models.load_model(p, compile=False)
        names = [layer.name for layer in self.model.layers]
        i = names.index("backbone")
        self._backbone = self.model.get_layer("backbone")
        self._head = self.model.layers[i + 1:]
        info = p.with_name("model_info.json")
        if info.exists():
            data = json.loads(info.read_text())
            self.version = data.get("version", self.version)
            self.threshold = float(data.get("threshold", 0.5))
        # warm-up so the first real request is fast
        self._run(np.zeros((1, 224, 224, 3), dtype="float32"))

    def _run(self, x: np.ndarray):
        tf = self._tf
        t = tf.convert_to_tensor(x / 127.5 - 1.0)
        with tf.GradientTape() as tape:
            conv = self._backbone(t, training=False)
            tape.watch(conv)
            h = conv
            for layer in self._head:
                h = layer(h, training=False)
            score = h[:, 0]
        grads = tape.gradient(score, conv)
        w = tf.reduce_mean(grads, axis=(1, 2))[0]
        cam = tf.nn.relu(tf.reduce_sum(conv[0] * w, axis=-1)).numpy()
        cam = cam / (cam.max() + 1e-8)
        return float(score.numpy()[0]), cam

    def predict(self, gray: np.ndarray) -> dict:
        if not self.ready:
            raise ModelNotReady("Model is not loaded. Train it first (see README).")
        proc = preprocess_gray(gray)
        x = to_model_input(proc)[None]
        with self._lock:
            prob, cam = self._run(x)
        stone = prob >= self.threshold
        heat = cv2.applyColorMap(np.uint8(255 * cv2.resize(cam, (proc.shape[1], proc.shape[0]))), cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(cv2.cvtColor(proc, cv2.COLOR_GRAY2BGR), 0.6, heat, 0.4, 0)
        ok, png = cv2.imencode(".png", overlay)
        return {
            "result": "Stone" if stone else "No Stone",
            "prob_stone": prob,
            "confidence": prob if stone else 1.0 - prob,
            "model_version": self.version,
            "cam_png": png.tobytes(),
        }


ml_service = MLService()
"""Must stay identical to ml/src/preprocess.py (same preprocessing as training)."""
import cv2
import numpy as np

IMG_SIZE = 224


def preprocess_gray(gray: np.ndarray) -> np.ndarray:
    gray = cv2.resize(gray, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    gray = cv2.medianBlur(gray, 3)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def to_model_input(gray224: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(gray224, cv2.COLOR_GRAY2RGB).astype("float32")
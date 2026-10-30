"""Shared preprocessing. backend/app/services/preprocess.py MUST stay identical."""
import cv2
import numpy as np

IMG_SIZE = 224


def preprocess_gray(gray: np.ndarray) -> np.ndarray:
    """gray: 2D uint8 image -> 224x224 uint8, denoised + contrast enhanced."""
    gray = cv2.resize(gray, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    gray = cv2.medianBlur(gray, 3)                       # reduce speckle noise
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)                             # local contrast


def to_model_input(gray224: np.ndarray) -> np.ndarray:
    """2D uint8 -> (224,224,3) float32 in 0..255 (scaling happens inside the model)."""
    return cv2.cvtColor(gray224, cv2.COLOR_GRAY2RGB).astype("float32")
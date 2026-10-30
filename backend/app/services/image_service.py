import io
import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

Image.MAX_IMAGE_PIXELS = 25_000_000   # blocks decompression bombs
ALLOWED_FORMATS = {"JPEG", "PNG"}
MAGIC = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")


class InvalidImage(ValueError):
    pass


def upload_dir() -> Path:
    p = Path(settings.UPLOAD_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_limited(fileobj, max_mb: int) -> bytes:
    data = fileobj.read(max_mb * 1024 * 1024 + 1)
    if len(data) > max_mb * 1024 * 1024:
        raise InvalidImage(f"Image is larger than {max_mb} MB")
    if not data:
        raise InvalidImage("Empty file")
    return data


def decode_image(data: bytes) -> np.ndarray:
    """Validate real content (not the file name) and return a grayscale uint8 array."""
    if not data.startswith(MAGIC):
        raise InvalidImage("Only JPG and PNG images are allowed")
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in ALLOWED_FORMATS:
                raise InvalidImage("Only JPG and PNG images are allowed")
            img.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise InvalidImage("File is not a valid image")
    gray = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_GRAYSCALE)
    if gray is None or min(gray.shape) < 32:
        raise InvalidImage("Image could not be read or is too small")
    return gray


def save_png(array: np.ndarray, suffix: str = "") -> str:
    """Re-encode (this drops EXIF/metadata) under a random name. Returns the file name."""
    name = f"{uuid.uuid4().hex}{suffix}.png"
    ok, buf = cv2.imencode(".png", array)
    if not ok:
        raise InvalidImage("Could not encode image")
    (upload_dir() / name).write_bytes(buf.tobytes())
    return name


def save_png_bytes(png: bytes, suffix: str = "") -> str:
    name = f"{uuid.uuid4().hex}{suffix}.png"
    (upload_dir() / name).write_bytes(png)
    return name


def safe_path(name: str) -> Path:
    p = (upload_dir() / name).resolve()
    if p.parent != upload_dir().resolve():
        raise InvalidImage("Bad file path")
    return p


def delete_file(name: str) -> None:
    try:
        safe_path(name).unlink(missing_ok=True)
    except InvalidImage:
        pass
import io
import importlib.util
from pathlib import Path

import cv2
import numpy as np


def png_bytes(shape=(224, 224), value=128):
    ok, encoded = cv2.imencode(".png", np.full(shape, value, dtype=np.uint8))
    assert ok
    return encoded.tobytes()


def test_model_training_and_serving_preprocessing_match():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "ml_preprocess_test", root / "ml" / "src" / "preprocess.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    image = np.random.default_rng(42).integers(0, 256, (319, 241), dtype=np.uint8)

    from app.services.preprocess import preprocess_gray

    np.testing.assert_array_equal(preprocess_gray(image), module.preprocess_gray(image))


def test_prediction_history_and_delete(client, auth_headers, monkeypatch):
    from app.services.ml_service import ml_service

    monkeypatch.setattr(
        ml_service,
        "predict",
        lambda _gray: {
            "result": "Stone",
            "confidence": 0.91,
            "prob_stone": 0.91,
            "model_version": "test-model",
            "cam_png": png_bytes(),
        },
    )
    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("scan.png", io.BytesIO(png_bytes()), "image/png")},
    )
    assert response.status_code == 201
    prediction = response.json()
    assert prediction["result"] == "Stone"

    history = client.get("/history", headers=auth_headers)
    assert history.status_code == 200
    assert [item["id"] for item in history.json()] == [prediction["id"]]

    image = client.get(f"/history/{prediction['id']}/image", headers=auth_headers)
    overlay = client.get(f"/history/{prediction['id']}/gradcam", headers=auth_headers)
    assert image.status_code == overlay.status_code == 200
    assert image.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert overlay.content.startswith(b"\x89PNG\r\n\x1a\n")

    deleted = client.delete(f"/history/{prediction['id']}", headers=auth_headers)
    assert deleted.status_code == 204
    assert client.get(f"/history/{prediction['id']}", headers=auth_headers).status_code == 404


def test_prediction_rejects_invalid_and_too_small_images(client, auth_headers):
    invalid = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("scan.png", io.BytesIO(b"not an image"), "image/png")},
    )
    assert invalid.status_code == 400

    tiny = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("tiny.png", io.BytesIO(png_bytes((16, 16))), "image/png")},
    )
    assert tiny.status_code == 400

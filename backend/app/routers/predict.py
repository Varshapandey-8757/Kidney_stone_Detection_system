from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.limiter import limiter
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionOut
from app.services import image_service as imgs
from app.services.ml_service import ModelNotReady, ml_service

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictionOut, status_code=201)
@limiter.limit("20/minute")
def predict(request: Request, file: UploadFile = File(...),
            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        data = imgs.read_limited(file.file, settings.MAX_UPLOAD_MB)
        gray = imgs.decode_image(data)
    except imgs.InvalidImage as e:
        raise HTTPException(400, str(e))
    try:
        out = ml_service.predict(gray)
    except ModelNotReady as e:
        raise HTTPException(503, str(e))

    image_name = imgs.save_png(gray)                       # re-encoded: metadata stripped
    cam_name = imgs.save_png_bytes(out["cam_png"], "_cam")
    row = Prediction(
        user_id=user.id, image_file=image_name, gradcam_file=cam_name,
        result=out["result"], confidence=out["confidence"], prob_stone=out["prob_stone"],
        model_version=out["model_version"],
    )
    db.add(row)
    db.commit()
    return row
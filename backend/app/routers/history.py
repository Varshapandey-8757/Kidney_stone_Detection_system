from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionOut
from app.services import image_service as imgs

router = APIRouter(prefix="/history", tags=["history"])


def _own(db: Session, pred_id: int, user: User) -> Prediction:
    # filtering by user_id means other people's records look like "not found"
    row = db.scalar(select(Prediction).where(Prediction.id == pred_id, Prediction.user_id == user.id))
    if row is None:
        raise HTTPException(404, "Not found")
    return row


@router.get("", response_model=list[PredictionOut])
def list_history(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                 db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = (select(Prediction).where(Prediction.user_id == user.id)
         .order_by(Prediction.created_at.desc()).limit(limit).offset(offset))
    return db.scalars(q).all()


@router.get("/{pred_id}", response_model=PredictionOut)
def get_one(pred_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _own(db, pred_id, user)


@router.get("/{pred_id}/image")
def get_image(pred_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FileResponse(imgs.safe_path(_own(db, pred_id, user).image_file), media_type="image/png")


@router.get("/{pred_id}/gradcam")
def get_gradcam(pred_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FileResponse(imgs.safe_path(_own(db, pred_id, user).gradcam_file), media_type="image/png")


@router.delete("/{pred_id}", status_code=204)
def delete_one(pred_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = _own(db, pred_id, user)
    imgs.delete_file(row.image_file)
    imgs.delete_file(row.gradcam_file)
    db.delete(row)
    db.commit()
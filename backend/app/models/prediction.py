from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.security import utcnow
from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    image_file: Mapped[str] = mapped_column(String(100))       # file name only, inside UPLOAD_DIR
    gradcam_file: Mapped[str] = mapped_column(String(100))
    result: Mapped[str] = mapped_column(String(20))            # "Stone" | "No Stone"
    confidence: Mapped[float] = mapped_column(Float)
    prob_stone: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
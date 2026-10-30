import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User
from app.routers import admin, auth, history, predict
from app.services.ml_service import ModelNotReady, ml_service

log = logging.getLogger("kidney")
logging.basicConfig(level=logging.INFO)


def seed_admin() -> None:
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD):
        return
    with SessionLocal() as db:
        email = settings.ADMIN_EMAIL.lower()
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(name="Admin", email=email, password_hash=hash_password(settings.ADMIN_PASSWORD), role="admin"))
            db.commit()
            log.info("Admin account created: %s", email)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    seed_admin()
    try:
        ml_service.load(settings.MODEL_PATH)
        log.info("Model loaded (%s)", ml_service.version)
    except ModelNotReady as e:
        log.warning("%s - /predict will return 503 until the model exists.", e)
    yield


app = FastAPI(
    title="Kidney Stone Detection API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_prod else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_prod else "/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,       # never "*" together with credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"          # medical images / tokens must not be cached
    if settings.is_prod:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if settings.COOKIE_SECURE:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(admin.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "model_loaded": ml_service.ready}
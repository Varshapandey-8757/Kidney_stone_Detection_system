from datetime import timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.limiter import limiter
from app.core.security import (DUMMY_HASH, create_access_token, hash_password, hash_refresh_token,
                               new_refresh_token, utcnow, verify_password)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import AuthOut, LoginIn, RegisterIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
COOKIE = "refresh_token"
INVALID = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")


def _set_cookie(response: Response, raw: str) -> None:
    response.set_cookie(
        COOKIE, raw,
        max_age=settings.REFRESH_TOKEN_DAYS * 86400,
        httponly=True, secure=settings.COOKIE_SECURE, samesite="lax",
        path=settings.REFRESH_COOKIE_PATH,
    )


def _issue(db: Session, user: User, response: Response) -> AuthOut:
    raw, hashed = new_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hashed,
                        expires_at=utcnow() + timedelta(days=settings.REFRESH_TOKEN_DAYS)))
    db.commit()
    _set_cookie(response, raw)
    return AuthOut(access_token=create_access_token(user.id, user.role), user=UserOut.model_validate(user))


@router.post("/register", response_model=AuthOut, status_code=201)
@limiter.limit("10/hour")
def register(request: Request, body: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Could not register with these details")
    user = User(name=body.name, email=body.email, password_hash=hash_password(body.password), role="user")
    db.add(user)
    db.commit()
    return _issue(db, user, response)


@router.post("/login", response_model=AuthOut)
@limiter.limit("5/minute")
def login(request: Request, body: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    ok = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not (user and ok and user.is_active):
        raise INVALID                      # same message for every failure
    return _issue(db, user, response)


@router.post("/refresh", response_model=AuthOut)
@limiter.limit("30/minute")
def refresh(request: Request, response: Response, db: Session = Depends(get_db),
            refresh_token: str | None = Cookie(default=None)):
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired")
    if not refresh_token:
        raise unauthorized
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token)))
    if row is None:
        raise unauthorized
    if row.revoked:
        # a rotated token was used again -> possible theft: revoke every session of this user
        db.execute(update(RefreshToken).where(RefreshToken.user_id == row.user_id).values(revoked=True))
        db.commit()
        raise unauthorized
    user = db.get(User, row.user_id)
    if row.expires_at < utcnow() or user is None or not user.is_active:
        raise unauthorized
    row.revoked = True                     # rotation: every refresh token is single-use
    db.commit()
    return _issue(db, user, response)


@router.post("/logout", status_code=204)
def logout(response: Response, db: Session = Depends(get_db),
           refresh_token: str | None = Cookie(default=None)):
    if refresh_token:
        row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token)))
        if row:
            row.revoked = True
            db.commit()
    response.delete_cookie(COOKIE, path=settings.REFRESH_COOKIE_PATH)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
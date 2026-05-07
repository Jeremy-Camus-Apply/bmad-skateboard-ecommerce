"""FastAPI dependencies (Story 1.5: chat authentication)."""

from __future__ import annotations

import json
import logging
import threading
from typing import Annotated

import firebase_admin
import jwt
from fastapi import Depends, HTTPException, Request, status
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

_firebase_init_lock = threading.Lock()


def _ensure_firebase_app(settings: Settings) -> None:
    """Initialize Firebase Admin exactly once per process when credentials exist."""

    if firebase_admin._apps:
        return

    raw = settings.secret_firebase_admin_credentials.strip()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase authentication is not configured",
        )

    with _firebase_init_lock:
        if firebase_admin._apps:
            return
        cred = credentials.Certificate(json.loads(raw))
        firebase_admin.initialize_app(cred)


async def require_chat_principal(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Verify Firebase ID token **or** anonymous session JWT and stamp `request.state`.

    - Firebase: `Authorization: Bearer <firebase-id-token>`
    - Anonymous: `X-Anonymous-Session: <jwt>` (optional `Bearer ` prefix)
    """

    authorization = request.headers.get("authorization")
    anonymous = request.headers.get("x-anonymous-session")

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
            )

        _ensure_firebase_app(settings)
        try:
            decoded = firebase_auth.verify_id_token(token, check_revoked=False)
        except firebase_auth.InvalidIdTokenError as exc:
            logger.info("firebase_invalid_id_token", extra={"error": str(exc)})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase ID token",
            ) from exc
        except firebase_auth.ExpiredIdTokenError as exc:
            logger.info("firebase_expired_id_token", extra={"error": str(exc)})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expired Firebase ID token",
            ) from exc
        except Exception as exc:  # pragma: no cover — defensive
            logger.exception("firebase_verify_failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firebase token verification failed",
            ) from exc

        uid = decoded.get("uid")
        if not isinstance(uid, str) or not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token payload"
            )

        request.state.user_id = uid
        request.state.anon_session_id = None
        return

    if anonymous:
        secret = settings.secret_anonymous_jwt_signing.strip()
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Anonymous sessions are not configured",
            )

        raw_token = anonymous.strip()
        if raw_token.lower().startswith("bearer "):
            raw_token = raw_token.split(" ", 1)[1].strip()

        try:
            payload = jwt.decode(raw_token, secret, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            logger.info("anonymous_jwt_invalid", extra={"error": str(exc)})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid anonymous session token",
            ) from exc

        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid anonymous session token",
            )

        request.state.user_id = None
        request.state.anon_session_id = sub
        return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.logging import logger


class AuthenticatedUser:
    def __init__(self, user_id: str, email: str, is_admin: bool = False, raw_claims: Optional[Dict[str, Any]] = None):
        self.id = user_id
        self.email = email
        self.is_admin = is_admin
        self.raw_claims = raw_claims or {}


def verify_supabase_jwt(token: str) -> AuthenticatedUser:
    """
    Verifies JWT token using local secret or JWKS public keys (§11).
    Avoids per-request remote API calls to preserve low latency.
    """
    try:
        # Development fallback / HMAC verification
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        user_id = payload.get("sub")
        email = payload.get("email", "")
        is_admin = payload.get("is_admin", False)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject (sub) claim"
            )

        return AuthenticatedUser(user_id=user_id, email=email, is_admin=is_admin, raw_claims=payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.PyJWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

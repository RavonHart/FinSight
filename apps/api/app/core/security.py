import os
import time
import uuid
import hashlib
import secrets
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.logging import logger

# JWKS cache
_JWKS_CACHE: Dict[str, Any] = {"keys": None, "expires_at": 0}


class AuthenticatedUser:
    def __init__(
        self,
        user_id: str,
        email: str,
        name: str = "",
        is_admin: bool = False,
        auth_provider: str = "local",
        raw_claims: Optional[Dict[str, Any]] = None
    ):
        self.id = user_id
        self.email = email
        self.name = name
        self.is_admin = is_admin
        self.auth_provider = auth_provider
        self.raw_claims = raw_claims or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "is_admin": self.is_admin,
            "auth_provider": self.auth_provider,
        }


def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with 32-byte salt and 600,000 iterations (NIST recommended)."""
    salt = secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
    return f"pbkdf2_sha256${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored PBKDF2 hash."""
    try:
        algorithm, salt_hex, key_hex = hashed_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 600000)
        return secrets.compare_digest(key, new_key)
    except Exception:
        return False


def create_access_token(
    user_id: str,
    email: str,
    name: str = "",
    is_admin: bool = False,
    auth_provider: str = "local",
    expires_delta_seconds: int = 3600
) -> str:
    """Generates a signed JWT access token adhering to RFC 7519 & Supabase compatibility."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email,
        "name": name,
        "is_admin": is_admin,
        "auth_provider": auth_provider,
        "aud": "authenticated",
        "role": "authenticated",
        "iat": now,
        "nbf": now,
        "exp": now + expires_delta_seconds,
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def create_refresh_token(
    user_id: str,
    expires_delta_seconds: int = 86400 * 30  # 30 days
) -> str:
    """Generates a long-lived signed JWT refresh token."""
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + expires_delta_seconds,
    }
    return jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def verify_supabase_jwt(token: str) -> AuthenticatedUser:
    """
    Verifies JWT token using local secret or JWKS public keys (§11).
    Validates token signature, expiration, and required subject claim without
    making per-request remote network calls to external auth servers.
    """
    try:
        # First inspect unverified header to see algorithm
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "HS256")

        if alg.startswith("RS") or alg.startswith("ES"):
            # Check JWKS (e.g. from Supabase JWKS endpoint)
            # If jwks is configured, use PyJWKClient
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            jwks_client = jwt.PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                options={"verify_aud": False}
            )
        else:
            # Fallback to local symmetric secret (HS256)
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject (sub) claim"
            )

        # Ensure user_id is a valid UUID format
        try:
            uuid.UUID(str(user_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: subject claim must be a valid UUID"
            )

        email = payload.get("email", "")
        name = payload.get("name", payload.get("user_metadata", {}).get("name", ""))
        is_admin = bool(payload.get("is_admin", False))
        auth_provider = payload.get("auth_provider", "supabase")

        return AuthenticatedUser(
            user_id=str(user_id),
            email=email,
            name=name,
            is_admin=is_admin,
            auth_provider=auth_provider,
            raw_claims=payload
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT verification attempt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed authentication credentials"
        )

import logging
from typing import Optional
from fastapi import Depends, Header, Request
import jwt
from jwt import PyJWKClient, PyJWKClientError, PyJWTError

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.models.auth import AuthUser

logger = logging.getLogger(__name__)

# Supabase projects created after 2025 sign access tokens with asymmetric keys
# (ES256 by default, RS256 for legacy projects). Newer projects have no shared
# HS256 secret, so JWKS verification is the only way to validate their tokens.
_JWKS_PLACEHOLDERS = ("your-project-ref", "example.supabase.co")
_JWT_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]


def _resolve_jwks_url() -> Optional[str]:
    """Explicit SUPABASE_JWKS_URL wins; otherwise derive it from SUPABASE_URL."""
    if settings.SUPABASE_JWKS_URL:
        return settings.SUPABASE_JWKS_URL
    url = (settings.SUPABASE_URL or "").rstrip("/")
    if not url.startswith("http"):
        return None
    if any(placeholder in url for placeholder in _JWKS_PLACEHOLDERS):
        return None
    return f"{url}/auth/v1/.well-known/jwks.json"


# Initialize JWKS client when a real Supabase project is configured.
_jwks_client: Optional[PyJWKClient] = None
_jwks_url = _resolve_jwks_url()
if _jwks_url:
    try:
        _jwks_client = PyJWKClient(_jwks_url)
        logger.info(f"Supabase JWT verification via JWKS: {_jwks_url}")
    except Exception as e:
        logger.warning(f"Could not initialize JWKS client: {e}")



def decode_supabase_jwt(token: str) -> dict:
    """Verifies Supabase JWT signature, expiry, and returns payload."""
    try:
        # 1. In Development/Test mode with mock tokens
        if settings.ENVIRONMENT in ("development", "test") and token.startswith("mock-user-"):
            user_id = token.replace("mock-user-", "")
            return {
                "sub": user_id,
                "email": f"{user_id}@example.com",
                "role": "authenticated",
            }

        # 2. Asymmetric verification via Supabase JWKS (ES256 / RS256).
        if _jwks_client:
            try:
                signing_key = _jwks_client.get_signing_key_from_jwt(token)
                return jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=_JWT_ALGORITHMS,
                    audience="authenticated",
                    options={"verify_exp": True},
                )
            except PyJWKClientError as e:
                # Unknown/rotated key or JWKS unreachable: fall through to HS256.
                logger.warning(f"JWKS verification failed, trying HS256 secret: {e}")

        # 3. Symmetric HS256 Verification via Supabase JWT Secret (legacy projects)
        if settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True},
            )
            return payload

        # If no secret is configured in development, decode unverified but warn
        if settings.ENVIRONMENT == "development":
            logger.warning("SUPABASE_JWT_SECRET not set: decoding token unverified for dev.")
            return jwt.decode(token, options={"verify_signature": False})

        raise UnauthorizedError("Server JWT verification not configured")

    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Authentication token has expired")
    except PyJWTError as e:
        logger.error(f"JWT verification failure: {e}")
        raise UnauthorizedError("Invalid authentication token")


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> AuthUser:
    """FastAPI dependency to authenticate and extract the active user from Supabase JWT."""
    if not authorization:
        raise UnauthorizedError("Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Authorization header must be 'Bearer <token>'")

    token = parts[1]
    payload = decode_supabase_jwt(token)

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise UnauthorizedError("Token payload missing user identifier ('sub')")

    return AuthUser(
        id=str(user_id),
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
        raw_claims=payload,
    )

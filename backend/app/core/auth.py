import logging
from typing import Optional
from fastapi import Depends, Header, Request
import jwt
from jwt import PyJWKClient, PyJWTError

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.models.auth import AuthUser

logger = logging.getLogger(__name__)

# Initialize JWKS client if URL is configured (for RS256 Supabase keys)
_jwks_client: Optional[PyJWKClient] = None
if settings.SUPABASE_JWKS_URL:
    try:
        _jwks_client = PyJWKClient(settings.SUPABASE_JWKS_URL)
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

        # 2. Asymmetric RS256 Verification via Supabase JWKS
        if _jwks_client:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="authenticated",
                options={"verify_exp": True},
            )
            return payload

        # 3. Symmetric HS256 Verification via Supabase JWT Secret
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

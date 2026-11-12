import logging
from typing import Optional, Tuple
from urllib.parse import urlparse

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
_JWKS_PLACEHOLDER_HOSTS = ("your-project-ref.supabase.co", "example.supabase.co")
_JWT_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]


def _resolve_jwks_url() -> Optional[str]:
    """Explicit SUPABASE_JWKS_URL wins; otherwise derive it from SUPABASE_URL.

    The value is normalised first (trimmed, scheme parsed case-insensitively) so
    copy-pasted env values with stray whitespace or an upper-case scheme still
    resolve correctly.
    """
    explicit = (settings.SUPABASE_JWKS_URL or "").strip()
    if explicit:
        parsed = urlparse(explicit)
        return explicit if parsed.scheme in ("http", "https") and parsed.hostname else None

    raw = (settings.SUPABASE_URL or "").strip().rstrip("/")
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None
    if parsed.hostname in _JWKS_PLACEHOLDER_HOSTS:
        return None
    return f"{parsed.scheme}://{parsed.netloc}/auth/v1/.well-known/jwks.json"


_jwks_client: Optional[PyJWKClient] = None
_jwks_url: Optional[str] = _resolve_jwks_url()
_jwks_error: Optional[str] = None


def _get_jwks_client() -> Optional[PyJWKClient]:
    """Lazily build the JWKS client so one transient failure isn't permanent."""
    global _jwks_client, _jwks_url, _jwks_error
    if _jwks_client is not None:
        return _jwks_client
    _jwks_url = _resolve_jwks_url()
    if not _jwks_url:
        _jwks_error = "SUPABASE_URL is not set or is not a valid http(s) URL"
        return None
    try:
        _jwks_client = PyJWKClient(_jwks_url)
        _jwks_error = None
        logger.info(f"Supabase JWT verification via JWKS: {_jwks_url}")
    except Exception as e:  # pragma: no cover - environment dependent
        _jwks_error = f"{type(e).__name__}: {e}"
        logger.warning(f"Could not initialize JWKS client: {e}")
    return _jwks_client


def jwks_diagnostic() -> Tuple[Optional[str], Optional[str]]:
    """(resolved JWKS URL, last error) for the /health endpoint."""
    _get_jwks_client()
    return _jwks_url, _jwks_error


def _usable_jwt_secret() -> Optional[str]:
    """The legacy HS256 secret, ignoring the placeholder baked into older images."""
    secret = settings.SUPABASE_JWT_SECRET
    if not secret or secret.startswith("placeholder"):
        return None
    return secret


def jwt_verification_mode() -> str:
    """Which JWT verification path is active (surfaced in /health)."""
    if _get_jwks_client():
        return "jwks"
    if _usable_jwt_secret():
        return "hs256"
    return "none"


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
        jwks_client = _get_jwks_client()
        if jwks_client:
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
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
        jwt_secret = _usable_jwt_secret()
        if jwt_secret:
            payload = jwt.decode(
                token,
                jwt_secret,
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

from urllib.parse import urlparse

from fastapi import APIRouter
from app.core.config import settings
from app.core.auth import jwks_diagnostic, jwt_verification_mode
from app.models.health import HealthResponse

router = APIRouter()


def _supabase_host() -> str:
    """Hostname of the configured Supabase project, or a marker if unset/placeholder."""
    url = (settings.SUPABASE_URL or "").strip()
    host = urlparse(url).hostname
    if not host:
        return "unset"
    if "your-project-ref" in host or host == "example.supabase.co":
        return "placeholder"
    return host


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def check_health() -> HealthResponse:
    """System health & observability check endpoint."""
    jwks_url, jwks_error = jwks_diagnostic()
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        commit=(settings.GIT_COMMIT or "unknown"),
        jwt_verification=jwt_verification_mode(),
        supabase_host=_supabase_host(),
        jwks_url=jwks_url or "unset",
        jwks_error=(jwks_error or "")[:200],
        components={
            "database": "operational",
            "mqtt_broker": "operational",
            "e2b_sandbox": "operational",
            "cloud_service": "operational",
        },
    )

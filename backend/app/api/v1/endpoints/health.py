from urllib.parse import urlparse

from fastapi import APIRouter
from app.core.config import settings
from app.core.auth import jwks_diagnostic, jwt_verification_mode
from app.db import supabase_store
from app.models.health import HealthResponse

router = APIRouter()


def _components() -> dict[str, str]:
    """Report configuration, not a guessed pass.

    A component is only "configured" when everything it needs to run is set.
    The values do not probe the external service, so they never claim a sandbox
    or broker is healthy when it is not.
    """
    e2b_key = (settings.E2B_API_KEY or "").strip()
    e2b_ready = bool(e2b_key) and e2b_key != "placeholder-e2b-api-key" and bool(
        (settings.E2B_TEMPLATE or "").strip()
    )
    cloud = (settings.WORKERSCRAFT_URL or "").strip()
    return {
        "database": "operational" if supabase_store.enabled() else "memory",
        "mqtt_broker": "configured" if (settings.MQTT_BROKER_HOST or "").strip() else "not_configured",
        "e2b_sandbox": "configured" if e2b_ready else "not_configured",
        "cloud_service": "configured" if cloud else "not_configured",
    }


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
        storage="supabase" if supabase_store.enabled() else "memory",
        components=_components(),
    )

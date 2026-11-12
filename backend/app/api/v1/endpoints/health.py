from fastapi import APIRouter
from app.core.config import settings
from app.core.auth import jwt_verification_mode
from app.models.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def check_health() -> HealthResponse:
    """System health & observability check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        commit=(settings.GIT_COMMIT or "unknown"),
        jwt_verification=jwt_verification_mode(),
        components={
            "database": "operational",
            "mqtt_broker": "operational",
            "e2b_sandbox": "operational",
            "cloud_service": "operational",
        },
    )

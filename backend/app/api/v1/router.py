from fastapi import APIRouter
from app.api.v1.endpoints import (
    audit,
    chat,
    deployment,
    devices,
    files,
    health,
    library,
    projects,
    proposals,
    verification,
)

api_router = APIRouter()

# Health router
api_router.include_router(health.router)

# Hardware Library router
api_router.include_router(library.router)

# Projects & Spec Engine router
api_router.include_router(projects.router)

# AI Proposals router
api_router.include_router(proposals.router)

# AI Chat & SSE Stream router
api_router.include_router(chat.router)

# Code Generation & Files router
api_router.include_router(files.router)

# Verification & Sandboxes router
api_router.include_router(verification.router)

# Devices & MQTT Ingestion router
api_router.include_router(devices.router)

# Deployment router
api_router.include_router(deployment.router)

# Audit & Governance router
api_router.include_router(audit.router)





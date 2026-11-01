from fastapi import APIRouter
from app.api.v1.endpoints import health, library, projects

api_router = APIRouter()

# Health router
api_router.include_router(health.router)

# Hardware Library router
api_router.include_router(library.router)

# Projects & Spec Engine router
api_router.include_router(projects.router)



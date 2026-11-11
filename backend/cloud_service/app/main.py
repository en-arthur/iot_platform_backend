from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import apps, auth, storage, files, admin

app = FastAPI(
    title="DeviceStack Cloud Service",
    description="Backend cloud service for generated IoT apps",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(apps.router)
app.include_router(auth.router)
app.include_router(storage.router)
app.include_router(files.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "service": "DeviceStack Cloud Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

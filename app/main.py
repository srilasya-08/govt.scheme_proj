from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.api.v1.endpoints import router as api_v1_router
from app.models.scheme import HealthResponse
from app.services.scheme_service import scheme_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "**Multilingual Government Scheme Finder Backend API**\n\n"
        "An Interdisciplinary Project (IDP) enabling beneficiaries across India "
        "to discover welfare and educational schemes through speech and text in Indian languages.\n\n"
        "### Key Modules:\n"
        "- 🏛️ **Scheme Catalog**: Verified database of Central and State schemes (Tamil Nadu, etc.)\n"
        "- 🔍 **Multi-criteria Filtering**: Filter by state, category, target beneficiary persona\n"
        "- 🌐 **Multilingual Ready**: Pre-indexed metadata in English, Tamil (தமிழ்), Telugu (తెలుగు), and Hindi (हिंदी)\n"
        "- ⚡ **Async High Performance**: Powered by modern Python and FastAPI\n"
    ),
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable Cross-Origin Resource Sharing (CORS) for frontend teammates
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
async def root():
    """Redirects visitors from root directly to interactive Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["Schemes & System"])
async def root_health():
    """Top-level health check endpoint."""
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        uptime_status="online",
        total_schemes_loaded=scheme_service.total_count,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

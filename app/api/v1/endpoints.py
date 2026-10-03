from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body, status

from app.core.config import settings
from app.models.scheme import (
    Scheme,
    SchemeFilter,
    SchemeSearchResponse,
    HealthResponse,
    UserProfile,
    EligibilityCheckResponse,
    ExtractedIntent,
    CatalogStats,
)
from app.services.scheme_service import scheme_service

router = APIRouter(tags=["Schemes & System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health & Status Check",
    description="Returns the health status of the backend API, application version, and the count of loaded schemes.",
)
async def check_health():
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        uptime_status="online",
        total_schemes_loaded=scheme_service.total_count,
    )


@router.get(
    "/stats",
    response_model=CatalogStats,
    summary="Scheme Catalog Analytics & Statistics",
    description="Provides real-time statistics including central vs state breakdown, distribution across sectors, and target beneficiaries.",
)
async def get_stats():
    return scheme_service.get_catalog_stats()


@router.get(
    "/schemes",
    response_model=SchemeSearchResponse,
    summary="List & Filter Government Schemes",
    description="Retrieve government schemes with optional filters for state, category, target beneficiary, or keyword search.",
)
async def list_schemes(
    state: Optional[str] = Query(None, description="Filter by state (e.g. 'Tamil Nadu', 'All India')"),
    category: Optional[str] = Query(None, description="Filter by sector (e.g. 'Education', 'Agriculture')"),
    beneficiary: Optional[str] = Query(None, description="Filter by persona (e.g. 'student', 'farmer', 'women')"),
    search: Optional[str] = Query(None, description="Free-text keyword search across titles, summaries, tags"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    return scheme_service.filter_schemes(
        state=state,
        category=category,
        beneficiary=beneficiary,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/schemes/{scheme_id}",
    response_model=Scheme,
    summary="Get Scheme Details by ID",
    description="Fetch complete scheme details, eligibility criteria, benefits, and required documents by scheme ID (e.g., TN-SCH-001).",
)
async def get_scheme_by_id(scheme_id: str):
    scheme = scheme_service.get_by_id(scheme_id)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' was not found in the catalog.",
        )
    return scheme


@router.post(
    "/schemes/search",
    response_model=SchemeSearchResponse,
    summary="Advanced Search with Filter Body",
    description="POST endpoint for filtering schemes using a JSON payload containing multi-criteria filters.",
)
async def search_schemes_post(filters: SchemeFilter):
    return scheme_service.filter_schemes(
        state=filters.state,
        category=filters.category,
        beneficiary=filters.beneficiary,
        search_query=filters.search,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.post(
    "/schemes/check-eligibility",
    response_model=EligibilityCheckResponse,
    summary="Evaluate User Eligibility for Schemes",
    description=(
        "Rule-based eligibility evaluation engine. Evaluates an applicant's demographic profile "
        "(age, gender, occupation, parent occupation, state, income) against the scheme catalog, "
        "returning confidence scores, matched criteria, and unmet conditions."
    ),
)
async def check_eligibility(profile: UserProfile):
    return scheme_service.evaluate_eligibility(profile)


@router.post(
    "/nlp/extract-entities",
    response_model=ExtractedIntent,
    summary="Multilingual Intent & Demographic Entity Parser",
    description=(
        "Parses unstructured natural language text in Tamil, Telugu, Hindi, or English. "
        "Extracts demographic intent (state, occupation, parent occupation, education) "
        "and produces a structured UserProfile ready for eligibility evaluation."
    ),
)
async def extract_entities(
    query_text: str = Body(
        ...,
        media_type="text/plain",
        description="User's natural language input in Tamil, Telugu, Hindi, or English",
        examples=["i am a student my father is a farmer in tamil nadu"],
    )
):
    return scheme_service.extract_intent_from_text(query_text)


@router.get(
    "/categories",
    response_model=List[str],
    summary="Get Available Scheme Categories",
    description="Returns a list of distinct sectors/categories (e.g. Education, Agriculture, Social Welfare).",
)
async def get_categories():
    return scheme_service.get_categories()


@router.get(
    "/states",
    response_model=List[str],
    summary="Get Available States",
    description="Returns a list of distinct states covered in the database catalog.",
)
async def get_states():
    return scheme_service.get_states()


@router.get(
    "/beneficiaries",
    response_model=List[str],
    summary="Get Target Beneficiary Personas",
    description="Returns a list of distinct target beneficiary groups (e.g. Student, Farmer, Women).",
)
async def get_beneficiaries():
    return scheme_service.get_beneficiaries()


@router.post(
    "/schemes/reload",
    summary="Reload Scheme Catalog",
    description="Reloads the JSON schemes catalog into memory without restarting the server.",
)
async def reload_schemes():
    count = scheme_service.load_schemes()
    return {"message": "Scheme catalog reloaded successfully", "total_schemes": count}

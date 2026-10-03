from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class EligibilityCriteria(BaseModel):
    gender: Optional[str] = "All"
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    occupation: Optional[str] = None
    parent_occupation: Optional[str] = None
    education_level: Optional[str] = None
    family_income_limit: Optional[float] = None  # in INR per annum
    landholding_limit: Optional[str] = None
    state: str = "All India"
    description: str


class BenefitDetails(BaseModel):
    benefit_type: str  # Direct Financial Assistance, Scholarship, Subsidy, In-kind
    amount: Optional[str] = None
    frequency: Optional[str] = None  # Monthly, Annual, One-time, Per Semester
    description: str


class Scheme(BaseModel):
    id: str = Field(..., description="Unique scheme identifier code")
    title: str = Field(..., description="Official scheme name in English")
    title_local: Dict[str, str] = Field(
        default_factory=dict,
        description="Scheme title in regional languages (e.g. {'ta': '...', 'te': '...', 'hi': '...'}"
    )
    ministry: str = Field(..., description="Government Ministry / Department in charge")
    level: str = Field(..., description="Central or State")
    state: str = Field(default="All India", description="State name or All India")
    category: str = Field(..., description="Sector e.g., Education, Agriculture, Social Welfare")
    target_beneficiaries: List[str] = Field(
        default_factory=list,
        description="Target personas e.g. student, farmer, women, youth"
    )
    summary: str = Field(..., description="Brief scheme summary in English")
    summary_local: Dict[str, str] = Field(
        default_factory=dict,
        description="Brief summary in regional languages"
    )
    eligibility: EligibilityCriteria
    benefits: BenefitDetails
    documents_required: List[str] = Field(default_factory=list)
    how_to_apply: str
    official_url: str
    tags: List[str] = Field(default_factory=list)


class SchemeFilter(BaseModel):
    state: Optional[str] = None
    category: Optional[str] = None
    beneficiary: Optional[str] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0


class SchemeSearchResponse(BaseModel):
    total: int
    count: int
    offset: int
    limit: int
    results: List[Scheme]
    applied_filters: Dict[str, Optional[str]]


class UserProfile(BaseModel):
    state: str = Field(default="Tamil Nadu", description="Applicant's state of residence")
    age: Optional[int] = Field(None, ge=1, le=100, description="Applicant's age")
    gender: Optional[str] = Field("All", description="Gender: Male, Female, Other, or All")
    occupation: Optional[str] = Field(None, description="Current occupation (e.g. Student, Farmer, Unemployed)")
    parent_occupation: Optional[str] = Field(None, description="Parent's occupation (e.g. Farmer, Agricultural Laborer)")
    education_level: Optional[str] = Field(None, description="Current education level (e.g. High School, Undergraduate, PG)")
    annual_family_income: Optional[float] = Field(None, description="Annual family income in INR")
    community: Optional[str] = Field(None, description="Social category (e.g. General, OBC, MBC, SC, ST)")
    landholding_acres: Optional[float] = Field(None, description="Family cultivable land in acres")


class EligibilityResult(BaseModel):
    scheme_id: str
    scheme_title: str
    scheme_level: str
    state: str
    category: str
    eligible: bool
    match_score: int = Field(..., ge=0, le=100, description="Confidence score percentage")
    matched_reasons: List[str]
    unmet_reasons: List[str]
    benefits_summary: str
    official_url: str


class EligibilityCheckResponse(BaseModel):
    total_evaluated: int
    eligible_count: int
    partially_eligible_count: int
    user_profile: UserProfile
    eligible_schemes: List[EligibilityResult]
    partially_eligible_schemes: List[EligibilityResult]


class ExtractedIntent(BaseModel):
    raw_query: str
    detected_language: str
    detected_state: Optional[str]
    detected_occupation: Optional[str]
    detected_parent_occupation: Optional[str]
    detected_education: Optional[str]
    detected_category: Optional[str]
    keywords: List[str]
    suggested_profile: UserProfile


class CatalogStats(BaseModel):
    total_schemes: int
    central_schemes: int
    state_schemes: int
    categories_breakdown: Dict[str, int]
    states_breakdown: Dict[str, int]
    target_beneficiaries_breakdown: Dict[str, int]


class HealthResponse(BaseModel):
    status: str
    project: str
    version: str
    uptime_status: str
    total_schemes_loaded: int

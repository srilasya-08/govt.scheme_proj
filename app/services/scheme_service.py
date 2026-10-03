import json
import re
from typing import List, Optional, Dict, Set
from pathlib import Path
from collections import Counter

from app.core.config import settings
from app.models.scheme import (
    Scheme,
    SchemeSearchResponse,
    UserProfile,
    EligibilityResult,
    EligibilityCheckResponse,
    ExtractedIntent,
    CatalogStats,
)


class SchemeService:
    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or settings.SCHEMES_FILE
        self._schemes: List[Scheme] = []
        self.load_schemes()

    def load_schemes(self) -> int:
        """Loads schemes from JSON storage into validated Pydantic models."""
        if not self.data_file.exists():
            self._schemes = []
            return 0

        with open(self.data_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            self._schemes = [Scheme(**item) for item in raw_data]

        return len(self._schemes)

    @property
    def total_count(self) -> int:
        return len(self._schemes)

    def get_all(self, limit: int = 50, offset: int = 0) -> SchemeSearchResponse:
        """Returns paginated list of all schemes."""
        results = self._schemes[offset : offset + limit]
        return SchemeSearchResponse(
            total=len(self._schemes),
            count=len(results),
            offset=offset,
            limit=limit,
            results=results,
            applied_filters={},
        )

    def get_by_id(self, scheme_id: str) -> Optional[Scheme]:
        """Finds a scheme by its unique ID."""
        scheme_id_clean = scheme_id.strip().upper()
        for scheme in self._schemes:
            if scheme.id.upper() == scheme_id_clean:
                return scheme
        return None

    def filter_schemes(
        self,
        state: Optional[str] = None,
        category: Optional[str] = None,
        beneficiary: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SchemeSearchResponse:
        """
        Filters schemes by state, category, target beneficiary, and search terms.
        Supports matching across English and regional text (Tamil, Telugu, Hindi).
        """
        filtered = self._schemes

        # Filter by State (includes 'All India' schemes when a specific state is requested)
        if state and state.strip():
            state_clean = state.strip().lower()
            filtered = [
                s for s in filtered
                if s.state.lower() == state_clean or s.state.lower() == "all india" or state_clean in s.state.lower()
            ]

        # Filter by Category
        if category and category.strip():
            cat_clean = category.strip().lower()
            filtered = [
                s for s in filtered
                if cat_clean in s.category.lower()
            ]

        # Filter by Beneficiary persona (student, farmer, women, etc.)
        if beneficiary and beneficiary.strip():
            b_clean = beneficiary.strip().lower()
            filtered = [
                s for s in filtered
                if any(b_clean in tb.lower() for tb in s.target_beneficiaries)
                or (s.eligibility.occupation and b_clean in s.eligibility.occupation.lower())
                or (s.eligibility.parent_occupation and b_clean in s.eligibility.parent_occupation.lower())
            ]

        # Free-text Search across title, local titles, summary, eligibility, and tags
        if search_query and search_query.strip():
            q_clean = search_query.strip().lower()
            matching_results = []
            
            for s in filtered:
                # Build searchable corpus for this scheme
                corpus_parts = [
                    s.title.lower(),
                    s.summary.lower(),
                    s.category.lower(),
                    s.ministry.lower(),
                    s.eligibility.description.lower(),
                    " ".join(s.tags).lower(),
                    " ".join(s.target_beneficiaries).lower(),
                ]
                
                # Add regional titles and summaries to corpus
                for local_title in s.title_local.values():
                    corpus_parts.append(local_title.lower())
                for local_summary in s.summary_local.values():
                    corpus_parts.append(local_summary.lower())
                
                if s.eligibility.parent_occupation:
                    corpus_parts.append(s.eligibility.parent_occupation.lower())
                    
                full_corpus = " ".join(corpus_parts)
                
                # Direct match or multi-word match
                tokens = q_clean.split()
                if q_clean in full_corpus or all(t in full_corpus for t in tokens):
                    matching_results.append(s)
                    
            filtered = matching_results

        total_matched = len(filtered)
        paged_results = filtered[offset : offset + limit]

        return SchemeSearchResponse(
            total=total_matched,
            count=len(paged_results),
            offset=offset,
            limit=limit,
            results=paged_results,
            applied_filters={
                "state": state,
                "category": category,
                "beneficiary": beneficiary,
                "search": search_query,
            },
        )

    def evaluate_eligibility(self, profile: UserProfile) -> EligibilityCheckResponse:
        """
        Rule-based eligibility engine that calculates eligibility match scores,
        qualifying criteria, and unmet conditions for a user profile.
        """
        eligible_schemes: List[EligibilityResult] = []
        partially_eligible: List[EligibilityResult] = []

        applicant_state = (profile.state or "All India").strip().lower()
        applicant_gender = (profile.gender or "All").strip().title()
        applicant_occ = (profile.occupation or "").strip().lower()
        applicant_parent_occ = (profile.parent_occupation or "").strip().lower()
        applicant_income = profile.annual_family_income
        applicant_age = profile.age

        for scheme in self._schemes:
            matched_reasons = []
            unmet_reasons = []
            total_checks = 0
            passed_checks = 0

            # 1. State check
            scheme_state = scheme.state.strip().lower()
            total_checks += 1
            if scheme_state == "all india" or scheme_state == applicant_state or applicant_state in scheme_state:
                passed_checks += 1
                matched_reasons.append(f"Region matches: Valid for {scheme.state}")
            else:
                unmet_reasons.append(f"Scheme is restricted to {scheme.state} (User in {profile.state})")

            # 2. Gender check
            scheme_gender = (scheme.eligibility.gender or "All").strip().title()
            if scheme_gender not in ("All", ""):
                total_checks += 1
                if applicant_gender == "All" or applicant_gender == scheme_gender:
                    passed_checks += 1
                    matched_reasons.append(f"Gender criteria met: {scheme_gender}")
                else:
                    unmet_reasons.append(f"Restricted to {scheme_gender} applicants (User is {applicant_gender})")

            # 3. Age check
            if scheme.eligibility.min_age or scheme.eligibility.max_age:
                total_checks += 1
                if applicant_age is not None:
                    min_ok = (scheme.eligibility.min_age is None) or (applicant_age >= scheme.eligibility.min_age)
                    max_ok = (scheme.eligibility.max_age is None) or (applicant_age <= scheme.eligibility.max_age)
                    if min_ok and max_ok:
                        passed_checks += 1
                        matched_reasons.append(f"Age {applicant_age} is within required range ({scheme.eligibility.min_age or 0} - {scheme.eligibility.max_age or 'No limit'})")
                    else:
                        unmet_reasons.append(f"Age {applicant_age} does not meet criteria ({scheme.eligibility.min_age or 0} - {scheme.eligibility.max_age or 'No limit'})")
                else:
                    # User didn't specify age, mark as conditional pass
                    passed_checks += 0.5
                    matched_reasons.append(f"Requires age between {scheme.eligibility.min_age or 0} and {scheme.eligibility.max_age or 'No limit'} (Age unstated)")

            # 4. Beneficiary / Occupation check
            target_bens = [b.lower() for b in scheme.target_beneficiaries]
            total_checks += 1
            if applicant_occ and any(applicant_occ in tb for tb in target_bens):
                passed_checks += 1
                matched_reasons.append(f"Target beneficiary matches: {profile.occupation}")
            elif any(b in ("general", "family", "worker") for b in target_bens):
                passed_checks += 1
                matched_reasons.append("Open to general citizens and families")
            elif not applicant_occ:
                passed_checks += 0.5
                matched_reasons.append(f"Requires target beneficiary: {', '.join(scheme.target_beneficiaries)}")
            else:
                unmet_reasons.append(f"Primary target is {', '.join(scheme.target_beneficiaries)} (User is {profile.occupation})")

            # 5. Parent Occupation check (Critical for farmers' children scholarships!)
            scheme_parent_occ = scheme.eligibility.parent_occupation
            if scheme_parent_occ:
                total_checks += 1
                scheme_p_occ_lower = scheme_parent_occ.lower()
                if applicant_parent_occ and (applicant_parent_occ in scheme_p_occ_lower or "farmer" in applicant_parent_occ and "farmer" in scheme_p_occ_lower):
                    passed_checks += 1
                    matched_reasons.append(f"Family background matches: Parent is a {profile.parent_occupation}")
                elif not applicant_parent_occ:
                    passed_checks += 0.5
                    matched_reasons.append(f"Special benefit for children of: {scheme_parent_occ}")
                else:
                    unmet_reasons.append(f"Requires parent to be {scheme_parent_occ} (User specified {profile.parent_occupation})")

            # 6. Income Ceiling check
            if scheme.eligibility.family_income_limit:
                total_checks += 1
                limit = scheme.eligibility.family_income_limit
                if applicant_income is not None:
                    if applicant_income <= limit:
                        passed_checks += 1
                        matched_reasons.append(f"Annual income ₹{applicant_income:,.0f} is within limit of ₹{limit:,.0f}")
                    else:
                        unmet_reasons.append(f"Income ₹{applicant_income:,.0f} exceeds limit of ₹{limit:,.0f}")
                else:
                    passed_checks += 0.5
                    matched_reasons.append(f"Income cap is ₹{limit:,.0f}/year (Income unstated)")

            score = int((passed_checks / max(total_checks, 1)) * 100)

            result_entry = EligibilityResult(
                scheme_id=scheme.id,
                scheme_title=scheme.title,
                scheme_level=scheme.level,
                state=scheme.state,
                category=scheme.category,
                eligible=(len(unmet_reasons) == 0 and score >= 70),
                match_score=score,
                matched_reasons=matched_reasons,
                unmet_reasons=unmet_reasons,
                benefits_summary=f"{scheme.benefits.benefit_type}: {scheme.benefits.amount or scheme.benefits.description}",
                official_url=scheme.official_url,
            )

            if result_entry.eligible:
                eligible_schemes.append(result_entry)
            elif score >= 50 or (len(unmet_reasons) <= 1 and score >= 40):
                partially_eligible.append(result_entry)

        # Sort by match score descending
        eligible_schemes.sort(key=lambda x: x.match_score, reverse=True)
        partially_eligible.sort(key=lambda x: x.match_score, reverse=True)

        return EligibilityCheckResponse(
            total_evaluated=len(self._schemes),
            eligible_count=len(eligible_schemes),
            partially_eligible_count=len(partially_eligible),
            user_profile=profile,
            eligible_schemes=eligible_schemes,
            partially_eligible_schemes=partially_eligible,
        )

    def extract_intent_from_text(self, text: str) -> ExtractedIntent:
        """
        Multilingual keyword intent extractor (Tamil, Telugu, Hindi, English).
        Parses raw text into an initial structured UserProfile.
        """
        raw_clean = text.strip()
        lower_text = raw_clean.lower()

        # Language Detection
        detected_lang = "English"
        if re.search(r"[\u0B80-\u0BFF]", raw_clean):
            detected_lang = "Tamil"
        elif re.search(r"[\u0C00-\u0C7F]", raw_clean):
            detected_lang = "Telugu"
        elif re.search(r"[\u0900-\u097F]", raw_clean):
            detected_lang = "Hindi"

        # State extraction
        detected_state = None
        if any(w in lower_text for w in ["tamil nadu", "tamilnadu", "தமிழ்நாடு", "తమిళనాడు", "तमिलनाडु"]):
            detected_state = "Tamil Nadu"
        elif any(w in lower_text for w in ["telangana", "தெலங்கானா", "తెలంగాణ", "तेलंगाना"]):
            detected_state = "Telangana"
        elif any(w in lower_text for w in ["andhra", "ஆந்திரா", "ఆంధ్ర", "आंध्र"]):
            detected_state = "Andhra Pradesh"

        # Occupation extraction
        detected_occ = None
        if any(w in lower_text for w in ["student", "studying", "college", "school", "மாணவன்", "மாணவி", "படிக்கிறேன்", "విద్యార్థి", "చదువుతున్నాను", "छात्र", "विद्यार्थी"]):
            detected_occ = "Student"
        elif any(w in lower_text for w in ["farmer", "farming", "agriculture", "விவசாயி", "உழவர்", "రైతు", "వ్యవసాయం", "किसान", "खेती"]):
            detected_occ = "Farmer"

        # Parent occupation extraction
        detected_parent_occ = None
        has_parent_keyword = any(w in lower_text for w in [
            "father", "mother", "parent", "parents", "dad",
            "தந்தை", "அப்பா", "பெற்றோர்",
            "తండ్రి", "నాన్న",
            "पिता", "पिताजी", "माता"
        ])
        has_farmer_keyword = any(w in lower_text for w in [
            "farmer", "farming", "agriculture",
            "விவசாயி", "உழவர்", "விவசாயம்",
            "రైతు", "వ్యవసాయం",
            "किसान", "खेती"
        ])

        if has_parent_keyword and has_farmer_keyword:
            detected_parent_occ = "Farmer"
        elif has_farmer_keyword and detected_occ == "Student":
            # Contextual inference: student query mentioning farmer refers to parent
            detected_parent_occ = "Farmer"

        # Gender extraction
        detected_gender = "All"
        if any(w in lower_text for w in ["girl", "female", "woman", "women", "மாணவி", "பெண்", "మహిళ", "అమ్మాయి", "महिला", "छात्रा"]):
            detected_gender = "Female"
        elif any(w in lower_text for w in ["boy", "male", "மாணவன்", "ஆண்", "అబ్బాయి", "छात्र", "लड़का"]):
            detected_gender = "Male"

        # Category extraction
        detected_cat = None
        if any(w in lower_text for w in ["scholarship", "education", "கல்வி", "படிப்பு", "స్కాలర్‌షిప్", "విద్య", "छात्रवृत्ति", "शिक्षा"]):
            detected_cat = "Education"
        elif any(w in lower_text for w in ["health", "hospital", "மருத்துவம்", "ஆரோக்கியம்", "ఆరోగ్యం", "स्वास्थ्य"]):
            detected_cat = "Health"
        elif any(w in lower_text for w in ["agriculture", "விவசாயம்", "వ్యవసాయం", "कृषि"]):
            detected_cat = "Agriculture"

        keywords = [word for word in re.findall(r"\w+", lower_text) if len(word) > 2]

        suggested_profile = UserProfile(
            state=detected_state or "Tamil Nadu",
            gender=detected_gender,
            occupation=detected_occ,
            parent_occupation=detected_parent_occ,
            community=None,
        )

        return ExtractedIntent(
            raw_query=raw_clean,
            detected_language=detected_lang,
            detected_state=detected_state,
            detected_occupation=detected_occ,
            detected_parent_occupation=detected_parent_occ,
            detected_education="Undergraduate" if detected_occ == "Student" else None,
            detected_category=detected_cat,
            keywords=keywords[:10],
            suggested_profile=suggested_profile,
        )

    def get_catalog_stats(self) -> CatalogStats:
        """Returns statistical distribution of schemes in catalog."""
        categories = Counter([s.category for s in self._schemes])
        states = Counter([s.state for s in self._schemes])
        central_count = sum(1 for s in self._schemes if s.level.lower() == "central")
        state_count = sum(1 for s in self._schemes if s.level.lower() == "state")

        beneficiaries_list = []
        for s in self._schemes:
            beneficiaries_list.extend([b.title() for b in s.target_beneficiaries])
        b_counter = Counter(beneficiaries_list)

        return CatalogStats(
            total_schemes=len(self._schemes),
            central_schemes=central_count,
            state_schemes=state_count,
            categories_breakdown=dict(categories),
            states_breakdown=dict(states),
            target_beneficiaries_breakdown=dict(b_counter),
        )

    def get_categories(self) -> List[str]:
        """Returns unique categories available in the scheme catalog."""
        categories: Set[str] = {s.category for s in self._schemes}
        return sorted(list(categories))

    def get_states(self) -> List[str]:
        """Returns unique states available in the scheme catalog."""
        states: Set[str] = {s.state for s in self._schemes}
        return sorted(list(states))

    def get_beneficiaries(self) -> List[str]:
        """Returns unique target beneficiary types."""
        beneficiaries: Set[str] = set()
        for s in self._schemes:
            for b in s.target_beneficiaries:
                beneficiaries.add(b.title())
        return sorted(list(beneficiaries))


scheme_service = SchemeService()

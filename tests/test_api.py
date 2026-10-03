"""
Automated Backend Test Suite for Review-1
Tests all endpoints using FastAPI TestClient without needing a live network port.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["total_schemes_loaded"] >= 14
    print(f"PASS: Health check endpoint passed. Schemes loaded: {data['total_schemes_loaded']}")


def test_list_schemes():
    response = client.get("/api/v1/schemes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 14
    assert len(data["results"]) >= 14
    print(f"PASS: Listing schemes passed. Total: {data['total']}")


def test_filter_by_state_tamil_nadu():
    response = client.get("/api/v1/schemes?state=Tamil+Nadu")
    assert response.status_code == 200
    data = response.json()
    states = {item["state"] for item in data["results"]}
    assert "Tamil Nadu" in states
    print(f"PASS: State filtering passed. Found {data['count']} schemes for Tamil Nadu.")


def test_filter_by_student_and_farmer():
    """
    Scenario Test:
    User is a student whose father is a farmer in Tamil Nadu.
    Uzhavar Pathukappu Thittam must be returned!
    """
    response = client.get("/api/v1/schemes?state=Tamil+Nadu&beneficiary=student&search=farmer")
    assert response.status_code == 200
    data = response.json()
    scheme_ids = [s["id"] for s in data["results"]]
    assert "TN-SCH-003" in scheme_ids, "Uzhavar Pathukappu Thittam should be matched!"
    print(f"PASS: Specific scenario (student + farmer parent in TN) matched: {scheme_ids}")


def test_get_scheme_by_id():
    response = client.get("/api/v1/schemes/TN-SCH-001")
    assert response.status_code == 200
    scheme = response.json()
    assert scheme["id"] == "TN-SCH-001"
    assert "Pudhumai Penn" in scheme["title"]
    assert "ta" in scheme["title_local"]
    assert "te" in scheme["title_local"]
    assert "hi" in scheme["title_local"]
    print(f"PASS: Scheme by ID passed: {scheme['title']}")


def test_get_scheme_not_found():
    response = client.get("/api/v1/schemes/INVALID-999")
    assert response.status_code == 404
    print("PASS: 404 response for invalid scheme ID verified.")


def test_check_eligibility_engine():
    """
    Evaluates rule engine for:
    Student (Male) whose parent is a farmer in Tamil Nadu.
    Should qualify for TN-SCH-003 (Uzhavar Pathukappu Thittam) and TN-SCH-002 (Tamil Pudhalvan),
    but be ineligible for TN-SCH-001 (Pudhumai Penn - restricted to female).
    """
    profile = {
        "state": "Tamil Nadu",
        "gender": "Male",
        "age": 19,
        "occupation": "Student",
        "parent_occupation": "Farmer",
        "education_level": "Undergraduate",
        "annual_family_income": 150000.0,
    }
    response = client.post("/api/v1/schemes/check-eligibility", json=profile)
    assert response.status_code == 200
    data = response.json()
    assert data["eligible_count"] > 0

    eligible_ids = [s["scheme_id"] for s in data["eligible_schemes"]]
    assert "TN-SCH-003" in eligible_ids, "Should qualify for Uzhavar Pathukappu Thittam!"

    # Pudhumai Penn should not be eligible for a male student
    assert "TN-SCH-001" not in eligible_ids

    # Find the Uzhavar result and check matched reasons
    uzhavar_res = next(s for s in data["eligible_schemes"] if s["scheme_id"] == "TN-SCH-003")
    assert uzhavar_res["match_score"] >= 80
    assert any("Farmer" in r for r in uzhavar_res["matched_reasons"])
    print(f"PASS: Eligibility check passed. Eligible schemes: {eligible_ids}")


def test_nlp_extract_entities_tamil():
    tamil_query = "நான் ஒரு மாணவன் என் தந்தை ஒரு விவசாயி தமிழ்நாடு"
    response = client.post(
        "/api/v1/nlp/extract-entities",
        content=tamil_query,
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_language"] == "Tamil"
    assert data["detected_occupation"] == "Student"
    assert data["detected_parent_occupation"] == "Farmer"
    assert data["detected_state"] == "Tamil Nadu"
    print("PASS: Tamil NLP entity extraction passed:", data["suggested_profile"])


def test_nlp_extract_entities_english():
    english_query = "i am a student my father is a farmer in the state of tamil nadu"
    response = client.post(
        "/api/v1/nlp/extract-entities",
        content=english_query,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detected_language"] == "English"
    assert data["detected_occupation"] == "Student"
    assert data["detected_parent_occupation"] == "Farmer"
    assert data["detected_state"] == "Tamil Nadu"
    print("PASS: English NLP entity extraction passed:", data["suggested_profile"])


def test_catalog_stats():
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_schemes"] >= 14
    assert data["central_schemes"] > 0
    assert data["state_schemes"] > 0
    assert "Education" in data["categories_breakdown"]
    assert "Tamil Nadu" in data["states_breakdown"]
    print(f"PASS: Catalog statistics passed. Total: {data['total_schemes']} (State: {data['state_schemes']}, Central: {data['central_schemes']})")


def test_metadata_endpoints():
    r_cat = client.get("/api/v1/categories")
    assert r_cat.status_code == 200
    assert "Education" in r_cat.json()

    r_states = client.get("/api/v1/states")
    assert r_states.status_code == 200
    assert "Tamil Nadu" in r_states.json()

    r_ben = client.get("/api/v1/beneficiaries")
    assert r_ben.status_code == 200
    assert "Student" in r_ben.json()
    assert "Farmer" in r_ben.json()
    print("PASS: Metadata endpoints (categories, states, beneficiaries) passed.")


if __name__ == "__main__":
    print("\nRunning Backend Review-1 Test Suite...\n" + "=" * 50)
    test_health_check()
    test_list_schemes()
    test_filter_by_state_tamil_nadu()
    test_filter_by_student_and_farmer()
    test_get_scheme_by_id()
    test_get_scheme_not_found()
    test_check_eligibility_engine()
    test_nlp_extract_entities_tamil()
    test_nlp_extract_entities_english()
    test_catalog_stats()
    test_metadata_endpoints()
    print("=" * 50 + "\nALL REVIEW-1 TESTS PASSED SUCCESSFULLY!\n")

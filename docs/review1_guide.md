# Multilingual Government Scheme Finder - Review-1 Comprehensive Guide

## 1. Project Overview & Problem Statement
Citizens and students across India—particularly in rural and non-English-speaking regions—face major barriers in accessing government welfare and educational schemes due to complex language barriers, scattered information portals, and lack of digital awareness.

This **Interdisciplinary Project (IDP)** develops an intelligent, voice-enabled, multilingual portal that empowers citizens to query welfare schemes using their natural regional dialect (Tamil, Telugu, Hindi, English). The backend processes queries, extracts demographic intent (e.g. *Student, Farmer parent, Tamil Nadu*), searches authentic schemes, evaluates eligibility, and presents actionable guidance.

---

## 2. 3-Tier System Architecture

```mermaid
flowchart TD
    subgraph Tier 1: Client & Presentation Tier
        UI[Web Interface / Mobile PWA]
        Mic[Web Speech Audio Receiver\n- Multilingual STT]
        UI -->|Natural Speech / Text\nTamil / Telugu / Hindi / English| Mic
    end

    subgraph Tier 2: Application Backend (Your Module - FastAPI)
        Server[FastAPI REST API Server]
        Router[API Router & CORS Middleware]
        Models[Pydantic V2 Data Models]
        Service[Scheme Query & Filtering Engine]
        EligibilityEngine[Rule-Based Eligibility Engine\nConfidence Scoring & Reasoning]
        NLPExtractor[Multilingual Entity & Intent Parser\nTA / TE / HI / EN Tokenizer]
        
        Server --> Router
        Router --> Service
        Router --> EligibilityEngine
        Router --> NLPExtractor
        Service --> Models
    end

    subgraph Tier 3: Intelligence & Knowledge Tier
        SchemeDB[(Verified Scheme Catalog\n14 Schemes - Central, TN, AP, TS)]
        AI_Module[AI Deep Reasoning & LLM Agent\n- Future Milestone: Weeks 2-3]
        Crawler[Live Web Crawler & Scraper\n- Future Milestone: Weeks 4-5]
        
        Service --> SchemeDB
        Service -.-> AI_Module
        Service -.-> Crawler
    end

    Mic -->|HTTP REST Requests| Server
    Service -->|Structured JSON Response| UI
```

---

## 3. Tech Stack Justification (Why FastAPI for Backend?)

| Feature | FastAPI | Traditional Flask | Why it matters for IDP |
| :--- | :--- | :--- | :--- |
| **Interactive API Docs** | Automatic Swagger (`/docs`) & ReDoc (`/redoc`) | Requires manual Swagger plugins | Allows live testing directly in front of review panel |
| **Data Validation** | Built-in Pydantic V2 typing | Manual request validation | Prevents crashes on malformed requests |
| **Async Concurrency** | Native `async` / `await` | Synchronous by default | Essential for upcoming AI model calls & web scraping |
| **Speed & Performance** | One of the fastest Python frameworks | Slower WSGI overhead | Smooth real-time speech responses |

---

## 4. Implemented API Endpoints (Review-1 Deliverables)

| Method | Endpoint | Description | Sample Query Parameters / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | System health and loaded scheme count | `None` |
| `GET` | `/api/v1/stats` | Analytics: distribution across states & sectors | `None` |
| `GET` | `/api/v1/schemes` | Filterable scheme catalog | `?state=Tamil+Nadu&beneficiary=student` |
| `GET` | `/api/v1/schemes/{id}` | Detailed scheme by unique ID | Path: `/api/v1/schemes/TN-SCH-001` |
| `POST`| `/api/v1/schemes/search` | Multi-criteria search payload | JSON: `{"state": "Tamil Nadu", "beneficiary": "student", "search": "farmer"}` |
| `POST`| `/api/v1/schemes/check-eligibility` | Evaluates applicant demographics against schemes | JSON: `UserProfile` (age, occupation, parent occupation, state, income) |
| `POST`| `/api/v1/nlp/extract-entities` | Multilingual entity extraction from free-text | Raw text: `"நான் ஒரு மாணவன் என் தந்தை ஒரு விவசாயி தமிழ்நாடு"` |
| `GET` | `/api/v1/categories` | List of all sectors/categories | `None` (returns `["Education", "Agriculture", ...]`) |
| `GET` | `/api/v1/states` | List of covered states | `None` (returns `["All India", "Tamil Nadu", ...]`) |
| `GET` | `/api/v1/beneficiaries`| List of target personas | `None` (returns `["Student", "Farmer", "Women", ...]`) |

---

## 5. Live Demo Script for the Review Panel

When the evaluators ask to see your progress:

### Step 1: Launch the Backend
- Double-click `run.bat` or run:
  ```powershell
  py -3 -m uvicorn app.main:app --reload
  ```
- Open your browser to **`http://127.0.0.1:8000/docs`**.

### Step 2: Show Catalog Statistics
- Expand `GET /api/v1/stats` $\rightarrow$ Click **"Try it out"** $\rightarrow$ Click **"Execute"**.
- Point out:
  - 14 verified schemes loaded.
  - Distribution across Central (5) and State (9) levels.
  - Sector breakdown: Education, Agriculture, Health, Skill Development.

### Step 3: Demonstrate Multilingual Entity Parser (`/nlp/extract-entities`)
- Expand `POST /api/v1/nlp/extract-entities`.
- Paste the Tamil query:
  ```text
  நான் ஒரு மாணவன் என் தந்தை ஒரு விவசாயி தமிழ்நாடு
  ```
- Click **"Execute"**.
- Show how the parser:
  - Detects language: **Tamil**.
  - Extracts applicant role: **Student**.
  - Extracts parent role: **Farmer**.
  - Extracts region: **Tamil Nadu**.
  - Generates a structured `suggested_profile`.

### Step 4: Demonstrate the Eligibility Engine (`/schemes/check-eligibility`)
- Expand `POST /api/v1/schemes/check-eligibility`.
- Test with this profile:
  ```json
  {
    "state": "Tamil Nadu",
    "gender": "Male",
    "age": 19,
    "occupation": "Student",
    "parent_occupation": "Farmer",
    "education_level": "Undergraduate",
    "annual_family_income": 150000
  }
  ```
- Click **"Execute"**.
- Highlight the intelligence:
  - **Eligible**: **TN-SCH-003: Chief Minister's Uzhavar Pathukappu Thittam** (Match score: 100%, reason: "Family background matches: Parent is a Farmer").
  - **Eligible**: **TN-SCH-002: Tamil Pudhalvan Scheme** (Match score: 100%, reason: "Gender criteria met: Male, State matches Tamil Nadu").
  - **Ineligible**: **TN-SCH-001: Pudhumai Penn** (Correctly rejected with reason: "Restricted to Female applicants (User is Male)").

### Step 5: Run Automated Unit Tests
- Open a terminal and run:
  ```powershell
  py -3 tests/test_api.py
  ```
- Show all **11 automated tests passing 100%**.

---

## 6. 6-Week Backend Roadmap (For Your Review PPT)

- **Week 1 (Review-1)**: [COMPLETED] Core Architecture, Pydantic Schemas, FastAPI REST API, Verified 14-Scheme Catalog, Rule-Based Eligibility Engine, and Multilingual Entity Extractor.
- **Weeks 2–3 (Review-2)**: AI Deep Intent & Reasoning Engine (integrating LLM via Google Gemini for complex dialogues and speech transcript nuance).
- **Weeks 4–5 (Review-3)**: Live Web Crawler & Portal Scraper Module (`BeautifulSoup` + authentic portal retrieval) & Multilingual translation.
- **Week 6 (Final Viva)**: Integration with Frontend microphone receiver, Text-to-Speech audio reader, and final deployment.

# JOB_APP_AUTO 🚀
> **Intelligent Job Application Assistant & Second Jobber Tracking Suite**  
> Tailored for Thai & Global Tech Boards: LinkedIn, JobsDB, JobThai, JobBKK, JobTopGun, and WorkVenture.

---

## 📌 Overview

**JOB_APP_AUTO** is a pair-programming job application automation system designed for early-career second jobbers. It streamlines the job hunt across Thailand's top platforms while managing personalized cover letters, resume attachments, expected salary matching (handling both priced and unpriced job postings), and history logging directly to your tracking CSV.

### 🌟 Key Capabilities

1. **Target Platforms Supported**:
   - 🔵 **LinkedIn**: Search queries, Easy Apply autofill payload, corporate portals.
   - 🟠 **JobsDB (by SEEK)**: Quick Apply prefill, direct search URL builder.
   - 🔴 **JobThai**: Apply Now & HR email application builder.
   - 🔵 **JobBKK**: Bangkok metro technology & engineering listings.
   - 🟢 **JobTopGun**: Super Resume & direct application payload.
   - 🟣 **WorkVenture**: Tech companies & modern startup applications.

2. **Expected Salary Intelligence (Solving the "No Price Tag" Problem)**:
   - **The Problem**: >70% of tech postings in Thailand omit price tags, marking them as *"Negotiable"*, *"ตามโครงสร้างบริษัท"*, or leaving them blank.
   - **The Solution**: 
     - **Dual Regex Parser**: Extracts Thai & English salary figures (e.g. `40,000 - 50,000 บาท`, `45k - 60k THB`, `40 - 50 K`).
     - **Smart Unpriced Mode**: Automatically benchmarks roles (e.g. AI/ML Engineer in Bangkok: 40k–65k THB), marks them as viable opportunities, and auto-prefills your expected salary (`40,000 - 45,000 THB (Negotiable)`).
     - **Interactive Controls**: Range sliders, custom brackets, and preset buttons.

3. **Authentic Tailored Cover Letter Engine**:
   - Synthesizes candidate background directly from `docs/aboutme.txt` and `docs/example_coverletter.txt`.
   - Automatically emphasizes matching experience based on domain:
     - **FinTech / Trading**: Emphasizes LINE Stock Analysis AI Agent and financial market logic.
     - **Computer Vision**: Emphasizes StaffLenz AI and Thai/Lao License Plate Recognition pipeline.
     - **GenAI / RAG**: Emphasizes Thai Legal RAG chatbot, LangGraph, and vector retrieval.
     - **Backend / Software**: Emphasizes FastAPI, Docker, GCP Cloud Run, and CI/CD.

4. **Bi-Directional CSV Synchronization**:
   - Live synced with `docs/Job Application - Second Jobber.csv` across all 18 standard tracking columns.
   - View, search, update status (e.g., `Draft` -> `Resume Sent` -> `Interview Scheduled` -> `Not Pass?`), and save customized cover letters into the `Job Letter` column.

5. **Quick Autofill Floating Bar**:
   - One-click copy for Candidate Name, Phone (`095-959-6921`), Email, Expected Salary, Resume PDF path, and Portfolio URL.

---

## 🛠️ Project Structure

```
JOB_APP_AUTO/
├── AGENTS.md                  # Project rules & guidelines
├── README.md                  # Documentation
├── requirements.txt           # Pinned dependencies
├── app.py                     # Web Dashboard & REST API entrypoint
├── main.py                    # CLI Orchestration entrypoint
├── docs/                      # Resumes, profiles, and CSV tracker
│   ├── Kwankhao_Sivasomboon_Resume.pdf
│   ├── Kwankhao_Sivasomboon_Resume.docx
│   ├── Job Application - Second Jobber.csv
│   ├── aboutme.txt
│   └── example_coverletter.txt
├── src/
│   ├── config.py              # Central settings, paths, and platform registry
│   ├── models.py              # Pydantic data schemas
│   ├── services/
│   │   ├── resume_service.py       # Candidate profile loader & PDF reader
│   │   ├── salary_matcher.py       # Thai/EN salary parser & unpriced strategy
│   │   ├── cover_letter_service.py # Tailored cover letter generator
│   │   ├── history_tracker.py      # CSV reader/writer (18 columns)
│   │   ├── scraper_service.py      # JD metadata extractor
│   │   └── platforms/              # Platform adapters (LinkedIn, JobsDB, etc.)
│   └── web/
│       ├── static/                 # CSS & JavaScript
│       └── templates/index.html    # Modern Dark Glassmorphism UI
└── tests/                          # Automated Pytest suite
    ├── test_salary_matcher.py
    ├── test_cover_letter_service.py
    ├── test_history_tracker.py
    └── test_platform_manager.py
```

---

## 🚀 Getting Started

### 1. Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Launching the Web Dashboard

```bash
# Option A: Via uvicorn
python3 -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload

# Option B: Via CLI
python3 main.py serve --port 8000
```
Open your browser at `http://127.0.0.1:8000`.

---

## 💻 CLI Orchestration

You can also run tasks directly from your terminal:

```bash
# 1. View Dashboard Stats from CSV
python3 main.py stats

# 2. Search Openings on Platforms
python3 main.py search --platform linkedin --keywords "AI Engineer" --open
python3 main.py search --platform jobsdb --keywords "Backend Engineer" --location "Bangkok"

# 3. Evaluate Salary Fit & Unpriced Postings
python3 main.py evaluate-salary --text "42,000 - 55,000 บาท" --role "AI Engineer"
python3 main.py evaluate-salary --text "Competitive salary and health insurance" --role "AI Engineer"

# 4. Generate Tailored Cover Letter
python3 main.py cover-letter --company "SCBX" --role "AI Engineer" --jd "Financial AI RAG agents"

# 5. Log Application into CSV
python3 main.py log-app --company "Agoda" --role "Software Engineer" --link "https://..." --status "Resume Sent"
```

---

## 🧪 Running Tests

```bash
python3 -m pytest tests/ -v
```

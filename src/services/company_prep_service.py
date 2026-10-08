"""Company Intelligence & Interview Presentation Preparation Service (Prep Agent).

Generates company research briefs, 5-slide presentation deck outlines,
and tailored interview talking points for jobs in 'Submitted' / 'Resume Sent' status.
"""

import urllib.parse
from typing import Dict, List, Optional

from src.models import (
    CompanyPrepReport,
    CompanyPrepRequest,
    InterviewQA,
    PresentationSlide,
)


class CompanyPrepService:
    """Prepares company intelligence and 5-slide interview presentation kits."""

    # Curated knowledge base for major Thai & regional employers in user's tracker
    KNOWN_COMPANIES: Dict[str, Dict[str, str]] = {
        "scb": {
            "category": "FinTech & Digital Banking",
            "overview": (
                "SCBX / SCB TechX is a leading financial technology group in Thailand driving the 'AI-First Bank' "
                "transformation across digital lending, wealth management, cloud-native microservices, and data platforms."
            ),
            "focus": "Scalable backend microservices (Go/Python), AI credit/risk modeling, RAG enterprise assistants, and cloud resilience.",
        },
        "kbank": {
            "category": "FinTech & Banking Innovation",
            "overview": (
                "Kasikornbank / KBTG / Kasikorn Labs leads regional banking technology, powering K PLUS and researching "
                "AI, quantitative finance, fraud detection, and next-generation customer analytics."
            ),
            "focus": "Production ML pipelines, financial data engineering, GenAI customer solutions, and high-throughput APIs.",
        },
        "ttb": {
            "category": "Digital Banking (ttb spark)",
            "overview": (
                "ttb spark is the technology and data innovation arm of TMBThanachart Bank, building personalized "
                "financial well-being features on the ttb touch platform."
            ),
            "focus": "AI personalization, mobile-first backend services, financial data analytics, and agile product delivery.",
        },
        "finnomena": {
            "category": "WealthTech & Investment Platform",
            "overview": (
                "Finnomena is Thailand's premier digital wealth management and investment advisory platform, connecting "
                "investors with mutual funds, stock analytics, and financial insights."
            ),
            "focus": "Financial market data pipelines, portfolio analytics, AI investment signals, and reliable web/backend APIs.",
        },
        "tisco": {
            "category": "Financial Services & Wealth Management",
            "overview": (
                "TISCO Financial Group specializes in retail lending, asset management, and digital advisory platforms "
                "backed by enterprise AI and data infrastructure."
            ),
            "focus": "AI platform engineering, model governance, cloud deployment, and financial data integration.",
        },
        "agoda": {
            "category": "Global Travel Tech & High-Scale Engineering",
            "overview": (
                "Agoda (Booking Holdings) operates one of Asia's largest engineering hubs in Bangkok, handling millions "
                "of real-time pricing, search, and booking transactions daily."
            ),
            "focus": "High-concurrency distributed systems, CI/CD automation, real-time data pipelines, and rigorous A/B experimentation.",
        },
        "makro": {
            "category": "Retail Tech & E-Commerce (CP Axtra / Makro PRO)",
            "overview": (
                "CP Axtra / Makro PRO builds Thailand's leading B2B/B2C omnichannel wholesale e-commerce ecosystem, "
                "integrating supply chain intelligence, AI search, and merchant analytics."
            ),
            "focus": "AI product engineering, intelligent search & recommendation (BM25/Vector), supply chain optimization, and rapid delivery.",
        },
        "ascend": {
            "category": "FinTech & Digital Ecosystem (TrueMoney / Ascend Group)",
            "overview": (
                "Ascend Group powers TrueMoney and regional digital financial services across Southeast Asia, serving "
                "millions of users with payments, micro-lending, and AI-driven products."
            ),
            "focus": "AI product development, fraud/risk analytics, scalable cloud APIs, and cross-functional product execution.",
        },
        "scg": {
            "category": "Industrial Conglomerate & Supply Chain AI (SCG / SCGP)",
            "overview": (
                "SCG and SCG Packaging (SCGP) leverage AI, IoT, computer vision, and optimization algorithms to modernize "
                "manufacturing, sourcing, and regional logistics."
            ),
            "focus": "AI sourcing & forecasting, industrial computer vision, RAG knowledge systems, and business stakeholder alignment.",
        },
        "auto x": {
            "category": "FinTech & Auto Lending / InsurTech (SCBX Group)",
            "overview": (
                "AUTO X (under SCBX Group, operating Ngern Chaiyo) provides accessible auto title loans and digital insurance "
                "products powered by automated credit and document processing."
            ),
            "focus": "Document OCR/LPR automation, insurance workflow automation, AI officer tools, and cloud backend services.",
        },
        "insurex": {
            "category": "InsurTech & Data Science",
            "overview": (
                "InsureX focuses on data-driven insurance products, risk modeling, and automated claims/underwriting workflows."
            ),
            "focus": "Predictive modeling, OCR/vision automation, customer analytics, and API integration.",
        },
        "shopee": {
            "category": "E-Commerce & Marketplace Operations",
            "overview": (
                "Shopee is Southeast Asia's leading e-commerce marketplace, relying on AI automation and operational excellence "
                "to optimize logistics, seller tools, and buyer experience."
            ),
            "focus": "AI process automation, cross-functional project delivery, data-driven KPIs, and scalable tooling.",
        },
    }

    def generate_prep_report(self, req: CompanyPrepRequest) -> CompanyPrepReport:
        """Generates a structured company intelligence and 5-slide presentation kit."""
        company = req.company_name.strip() or "Target Company"
        position = req.job_position.strip() or "AI / Software Engineer"
        jd = (req.job_description or "").strip()
        comp_lower = company.lower()
        pos_lower = position.lower()
        jd_lower = jd.lower()

        # 1. Identify Company Profile & Domain
        matched_info = None
        for key, info in self.KNOWN_COMPANIES.items():
            if key in comp_lower:
                matched_info = info
                break

        if matched_info:
            industry_cat = matched_info["category"]
            overview = matched_info["overview"]
            focus_summary = matched_info["focus"]
        else:
            if any(w in comp_lower or w in jd_lower for w in ["bank", "fintech", "finance", "capital", "invest", "insur"]):
                industry_cat = req.industry or "FinTech & Financial Services"
                focus_summary = "Financial data pipelines, AI decision support, security, and reliable backend APIs."
            elif any(w in pos_lower or w in jd_lower for w in ["vision", "camera", "image", "iot"]):
                industry_cat = req.industry or "AI & Computer Vision Technology"
                focus_summary = "Real-time inference, edge/cloud deployment, model accuracy vs. latency trade-offs."
            else:
                industry_cat = req.industry or "Enterprise Technology & AI Solutions"
                focus_summary = "Production AI/ML services, scalable FastAPI/Docker microservices, and business workflow integration."

            overview = (
                f"{company} is hiring a {position} within the {industry_cat} sector. "
                f"The role emphasizes {focus_summary.lower()}"
            )

        # 2. Select Primary & Secondary Projects to Showcase on Slides 2 & 3
        is_fintech = any(w in industry_cat.lower() or w in jd_lower for w in ["fintech", "bank", "wealth", "finance", "stock", "insur"])
        is_vision = any(w in pos_lower or w in jd_lower or w in comp_lower for w in ["vision", "yolo", "camera", "plate", "auto x", "ocr"])

        if is_fintech:
            proj1_title = "Case Study 1: LINE Stock Analysis AI Agent (FinTech & LLM)"
            proj1_sub = "Combining Financial Data, Technical Indicators & News for Decision Support"
            proj1_bullets = [
                "Problem: Retail investors struggle to synthesize financial statements, price action, and breaking news quickly.",
                "Architecture: Python backend integrating market data APIs + LLM structured reasoning (Positive / Negative / Watch signals).",
                "Security & Cloud: Deployed on GCP Cloud Run with Firestore persistence and API keys secured via GCP Secret Manager.",
                f"Relevance to {company}: Demonstrates domain passion for financial analysis combined with production cloud engineering.",
            ]
        elif is_vision:
            proj1_title = "Case Study 1: StaffLenz AI & Multi-Stage Thai/Lao LPR Pipeline"
            proj1_sub = "Production Computer Vision Optimized for Real-World Edge & CPU Deployment"
            proj1_bullets = [
                "StaffLenz AI: Multi-camera RTSP workplace analytics using YOLOv11-Pose, InsightFace embeddings, and OpenVINO FP16.",
                "Thai/Lao LPR API: Sequential pipeline (PicoDet-S, D-FINE, MobileNetV2, ResNet18, CTC OCR fallback) with 4-point rectification.",
                "Measured Impact: Evaluated on 1,872 real plates — achieved 81.80% character recall and 92.47% Thai province accuracy on CPU.",
                f"Relevance to {company}: Proven ability to benchmark models, handle noisy real-world inputs, and ship on GCP Cloud Run.",
            ]
        else:
            proj1_title = "Case Study 1: Thai Legal RAG Chatbot & Hybrid Retrieval System"
            proj1_sub = "Agentic Workflow with Dense Vectors, BM25 & Reciprocal Rank Fusion"
            proj1_bullets = [
                "Problem: Standard LLM chat hallucinates on strict Thai legal articles requiring exact clause retrieval.",
                "Architecture: Hybrid search (Pinecone dense vectors + BM25 lexical search + RRF) orchestrated via LangGraph state machines.",
                "Reliability: Built-in response validation, fallback LLM routing, and containerized deployment on GCP Cloud Run.",
                f"Relevance to {company}: Directly applicable to enterprise knowledge retrieval, AI agents, and reliable production APIs.",
            ]

        proj2_title = "Case Study 2: End-to-End Backend, Cloud CI/CD & Automated QA"
        proj2_sub = "Production Engineering at Yourhome Platform & Personal Systems"
        proj2_bullets = [
            "Backend & APIs: Designed RESTful services with Python, FastAPI, Pydantic validation, and SQL/Firestore databases.",
            "Cloud DevOps: Configured Docker containerization, Google Cloud Build CI/CD, Artifact Registry, and Cloud Run auto-scaling.",
            "AI-Assisted QA: Built Thai speech/text-to-search pipelines and automated backend/UI testing workflows using Playwright.",
            "Engineering Mindset: Focus on maintainability, latency vs. accuracy trade-offs, and clear documentation.",
        ]

        # 3. Build 5-Slide Presentation Deck
        slides: List[PresentationSlide] = [
            PresentationSlide(
                slide_number=1,
                title=f"Kwankhao Sivasomboon — Candidate Pitch for {company}",
                subtitle=f"Target Role: {position} | Bridging Engineering, AI & Business Impact",
                bullet_points=[
                    "Education: B.Eng. in Survey Engineering, Chulalongkorn University (Strong spatial, mathematical & analytical foundation).",
                    "Core Stack: Python, FastAPI, Docker, GCP (Cloud Run, Firestore, Secret Manager), SQL, PyTorch, OpenCV/YOLO, LangGraph/RAG.",
                    "Unique Value: An engineer who connects technical architecture with financial/business logic rather than building tech in isolation.",
                    f"Why {company}: Excited to contribute to {industry_cat} by delivering practical, measurable systems.",
                ],
                speaker_notes=(
                    f"Open by thanking the {company} team. Highlight how transitioning from Chulalongkorn Survey Engineering "
                    "into AI Engineering built strong problem-solving habits and end-to-end ownership."
                ),
            ),
            PresentationSlide(
                slide_number=2,
                title=proj1_title,
                subtitle=proj1_sub,
                bullet_points=proj1_bullets,
                speaker_notes="Walk through the problem, system architecture diagram, trade-offs evaluated, and quantitative metrics.",
            ),
            PresentationSlide(
                slide_number=3,
                title=proj2_title,
                subtitle=proj2_sub,
                bullet_points=proj2_bullets,
                speaker_notes="Emphasize that you don't just train models in notebooks—you containerize, test, and deploy them to production.",
            ),
            PresentationSlide(
                slide_number=4,
                title=f"How I Will Add Value to {company}",
                subtitle="Connecting Technical Execution with Business Trade-Offs",
                bullet_points=[
                    f"Domain Alignment: {focus_summary}",
                    "Pragmatic Engineering: Selecting the right tool (whether rule-based, classical ML, or LLM/RAG) based on cost, latency, and ROI.",
                    "Cross-Functional Communication: Translating business requirements from PMs/analysts into clean API contracts and testable milestones.",
                    "Fast Adaptability: Proven track record of independently mastering new stacks (e.g., Go, distributed queues, or custom frameworks).",
                ],
                speaker_notes=f"Connect your background directly to {company}'s current roadmap and pain points mentioned in the JD.",
            ),
            PresentationSlide(
                slide_number=5,
                title=f"30-60-90 Day Contribution Plan at {company}",
                subtitle=f"Structured Onboarding & Impact Roadmap as {position}",
                bullet_points=[
                    "Days 1–30 (Learn & Align): Master codebase, CI/CD pipelines, data schemas, and ship initial bug fixes / unit tests.",
                    "Days 31–60 (Build & Integrate): Take ownership of a core feature, API module, or AI workflow; collaborate on code reviews.",
                    "Days 61–90 (Optimize & Scale): Improve inference/API performance, enhance monitoring/QA coverage, and propose data-backed improvements.",
                    "Q&A Discussion: What does success look like for this role in the first 6 months?",
                ],
                speaker_notes="Conclude with confidence and invite technical questions from the interview panel.",
            ),
        ]

        # 4. Build Targeted Interview Q&A
        qas: List[InterviewQA] = [
            InterviewQA(
                question=f"Why are you transitioning from Survey Engineering to {position} at {company}?",
                key_talking_points=(
                    "Survey Engineering at Chulalongkorn taught me geospatial data science, mathematical modeling, and sensor processing. "
                    "Through my internship at SKYVIV (drone crack detection & crop-yield ML) and my role as AI Engineer at Yourhome Platform, "
                    "I proved I can build and deploy full-stack AI systems on GCP Cloud Run."
                ),
            ),
            InterviewQA(
                question="Tell us about a time you had to balance model accuracy against system speed or cost.",
                key_talking_points=(
                    "In my Thai/Lao License Plate Recognition API, running heavy vision models on CPU was too slow. I benchmarked multiple "
                    "architectures and designed a sequential pipeline (PicoDet-S + D-FINE + MobileNetV2 + ResNet18 with 4-point rectification "
                    "and CTC OCR fallback), achieving 81.80% character recall and 92.47% province accuracy on CPU Cloud Run."
                ),
            ),
            InterviewQA(
                question=f"How do you ensure reliability when deploying LLM / AI services for {company}?",
                key_talking_points=(
                    "I use Pydantic for strict schema validation, hybrid retrieval (BM25 + dense vectors) to ground responses, "
                    "fallback model routing when primary APIs fail, Secret Manager for credentials, and Playwright for automated QA."
                ),
            ),
        ]

        # 5. Build Research Links
        q_comp = urllib.parse.quote(company)
        q_role = urllib.parse.quote(f"{company} {position}")
        research_links = [
            {
                "label": f"{company} Official & News Search",
                "url": f"https://www.google.com/search?q={q_comp}+Thailand+news+technology",
            },
            {
                "label": f"{company} on LinkedIn",
                "url": f"https://www.linkedin.com/search/results/companies/?keywords={q_comp}",
            },
            {
                "label": f"{company} Interview & Culture Reviews",
                "url": f"https://www.google.com/search?q={q_role}+interview+glassdoor+pantip",
            },
            {
                "label": f"{company} Tech Stack & Engineering",
                "url": f"https://www.google.com/search?q={q_comp}+engineering+tech+stack+blog",
            },
        ]

        # 6. Generate Markdown Presentation Deck
        md_lines = [
            f"# Interview & Presentation Prep Kit: {company}",
            f"**Role:** {position} | **Category:** {industry_cat}",
            "",
            "## 1. Company Intelligence Brief",
            f"- **Overview:** {overview}",
            f"- **Key Focus Areas:** {focus_summary}",
            "",
            "---",
            "## 2. 5-Slide Presentation Outline",
        ]
        for s in slides:
            md_lines.append(f"\n### Slide {s.slide_number}: {s.title}")
            md_lines.append(f"*{s.subtitle}*")
            for b in s.bullet_points:
                md_lines.append(f"- {b}")
            md_lines.append(f"\n> **Speaker Note:** {s.speaker_notes}")

        md_lines.append("\n---\n## 3. Key Interview Q&A Strategy")
        for idx, qa in enumerate(qas, 1):
            md_lines.append(f"\n**Q{idx}: {qa.question}**")
            md_lines.append(f"- **Strategy:** {qa.key_talking_points}")

        return CompanyPrepReport(
            company_name=company,
            job_position=position,
            industry_category=industry_cat,
            company_overview=overview,
            strategic_alignment=focus_summary,
            key_focus_areas=[s.strip() for s in focus_summary.split(",") if s.strip()],
            research_links=research_links,
            presentation_slides=slides,
            interview_qas=qas,
            markdown_deck="\n".join(md_lines),
            engine_used="smart_prep_agent",
        )

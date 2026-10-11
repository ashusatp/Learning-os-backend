# 🧠 Learning OS — Backend

> **An intelligent, structured learning operating system and adaptive revision platform designed for competitive exam preparation and deep conceptual mastery.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-orange.svg?style=flat)](https://alembic.sqlalchemy.org)

---

## 📖 What is Learning OS?

Preparing for high-stakes competitive examinations (such as JEE, NEET, UPSC, GATE, etc.) is rarely just about reading material—it is about **retention, error analysis, consistent revision, and active practice**.

Most students suffer from:
- **Unstructured knowledge**: Notes scattered across loose papers, drives, and bookmarks.
- **The forgetting curve**: Forgetting topics weeks after learning them because revisions aren't systematically scheduled.
- **Repeat mistakes**: Making the same calculation or conceptual blunders repeatedly without deep root-cause logging.
- **Cramming without strategy**: Lack of structured revision sprints tailored to exam countdowns.

**Learning OS** solves this by combining a **hierarchical syllabus structure**, **digital notes & whiteboards**, an **advanced spaced repetition engine (extended SM-2)**, a **dedicated mistake notebook**, a **practice question bank**, **interleaved revision campaigns**, and an **in-context AI tutor** into a cohesive system.

---

## ✨ Key Features

### 1. 🗂️ Hierarchical Curriculum Architecture
Organize syllabus content cleanly through a 4-tier knowledge hierarchy:
- **Goals**: Target milestones and examinations (e.g., *"JEE Advanced 2026"*).
- **Subjects**: Academic domains under a goal (e.g., *Physics, Mathematics, Chemistry*).
- **Topics**: Major curricular units (e.g., *Rotational Dynamics, Organic Chemistry*).
- **Subtopics**: Atomic learning nodes (e.g., *Moment of Inertia of Rigid Bodies*).
  - Drag-and-drop custom reordering across all levels.
  - Archive/restore mechanism to keep views uncluttered.

---

### 2. 📝 Rich Notes, Whiteboards & File Storage
Each subtopic serves as an all-in-one knowledge workspace:
- **Rich Text Notes**: Full HTML-formatted notes compatible with rich text editors (Tiptap / ProseMirror).
- **Interactive Sketchboards & Whiteboards**: Built-in multi-canvas support storing vector/JSON whiteboard data per subtopic.
- **Hierarchical Document Management**: Create nested folder trees within any subtopic and upload reference materials, PDFs, and cheatsheets.
- **Exam Weightage Metadata**: Track marks per question and past exam frequency per subtopic.

---

### 3. 🔁 Adaptive Spaced Repetition Engine (Extended SM-2)
An intelligent revision scheduling algorithm designed specifically for competitive exam retention:
- **Mastery Level Progression**:
  - `NOT_STARTED` ➔ `BEGINNER` ➔ `INTERMEDIATE` ➔ `ADVANCED` ➔ `MASTERED`.
  - Base intervals scale dynamically with mastery status (1 day up to 7+ days).
  - Automated promotion criteria based on consecutive streaks, mistake thresholds, and confidence ratings.
- **Quality Ratings**: Grade each revision session (`AGAIN`, `HARD`, `GOOD`, `EASY`) to adapt the SuperMemo ease factor ($1.3 \le EF \le 3.5$) and next review interval.
- **Mistake Urgency Multipliers**: Topics with frequent *conceptual* or *calculation* mistakes automatically jump higher in urgency.
- **Overdue Penalty Tiers**: Multi-tiered decay penalties (Grace ➔ Mild ➔ Significant ➔ Severe ➔ Critical) when revisions are missed.
- **Streak & Habit Tracking**:
  - Daily review streak counters and longest streak records.
  - Timezone-aware day boundaries (`Asia/Kolkata` configurable).
  - Streak freeze protections and vacation mode pauses.
  - Daily review limit caps and catch-up day pacing.
- **Visual Analytics**:
  - Daily priority revision queue sorted by real-time urgency scores.
  - Interactive monthly revision calendar.
  - Activity heatmap (GitHub-style) displaying consistency across months.

---

### 4. 🚀 Revision Campaigns Engine (Exam Sprints)
Plan and execute focused, high-intensity study sprints leading up to mock tests or exams:
- **Campaign Types**:
  - `SUBTOPIC_REVISION`: Comprehensive theory and notes review.
  - `MISTAKE_REVIEW`: Focused blitz on unresolved mistakes.
  - `PYQ_PRACTICE`: Practice marathon of Previous Year Questions.
- **Flexible Scoping**: Target entire subjects or select individual topics.
- **Interleaved Scheduling**: Study multiple subjects in parallel (interleaving) rather than monotonous single-subject blocks.
- **Interactive Preview**: Preview daily study schedules, target items per day, and subject distributions before committing to the database.
- **Progress Tracking**: Day-by-day checklist, progress bars, pause, resume, and item completion tracking.

---

### 5. 🎯 Comprehensive Question Bank & PYQ Tracker
An integrated practice database attached directly to subtopics:
- **Multiple Question Formats**:
  - Single Choice MCQ (`SINGLE_MCQ`)
  - Multiple Choice MCQ (`MULTI_MCQ`)
  - Numerical Value with tolerance (`NUMERICAL`)
  - True / False (`TRUE_FALSE`)
  - Subjective / Long Answer (`SUBJECTIVE`)
- **Rich Explanations & LaTeX**: HTML text and detailed step-by-step solutions supporting mathematical notation and images.
- **Exam Scoring Model**: Custom positive marks and negative mark deductions.
- **Tagging & Filtering**: Previous Year Question (`is_pyq`) badges, difficulty ratings (`EASY`, `MEDIUM`, `HARD`), and custom topic tags.
- **Cross-Level Retrieval**: Filter and paginate questions by Subtopic or across an entire Goal.

---

### 6. 🔍 Surgical Mistake Notebook
Turn mistakes into your biggest learning asset instead of repeating them:
- **Mistake Categorization**:
  - `CONCEPTUAL` (understanding gaps)
  - `CALCULATION` (math / algebraic slips)
  - `MISREAD` (reading comprehension errors)
  - `TIME_PRESSURE` (rushed decisions)
  - `SILLY` (careless missteps)
  - `OTHER`
- **Question Linking**: Directly link any mistake to the exact question where it occurred.
- **Deep Post-Mortem**: Separate rich HTML fields for *what went wrong* (`description_html`) and *the correct concept/method* (`correction_html`).
- **Resolution Lifecycle**: Track unresolved vs. resolved mistakes, log revision counts per mistake, and schedule repeat reviews.

---

### 7. 🤖 Context-Aware AI Study Assistant
A streaming AI tutor integrated into the learning workflow:
- **Multi-Provider AI Architecture**: Pluggable provider system supporting:
  - **OpenAI** (`gpt-4o-mini`, `gpt-4o`)
  - **Anthropic** (`claude-sonnet-4-20250514`, `claude-3-5-sonnet`)
  - **Google Gemini** (`gemini-2.0-flash`)
- **Real-Time Streaming**: Server-Sent Events (SSE) streaming responses directly into the client.
- **Deep Context Injection**: The AI assistant receives the exact hierarchical path (`Goal > Subject > Topic > Subtopic`), the student's active notes HTML, and any selected/highlighted text.
- **Editor-Ready Output**: Generates clean semantic HTML (tables, headings, bullet lists, callouts, mnemonics) ready for direct insertion into notes.
- **Account Controls**: Tiered plan management (`free`, `pro`), daily quota tracking, and per-minute rate limiting.

---

### 8. 🔐 Authentication & Account Management
- **Email & Password**: Secure password hashing with `bcrypt`.
- **Google OAuth 2.0**: One-click Google sign-in.
- **JWT Authentication**: Stateless authorization with configurable expiration.
- **Password Recovery**: Secure token-based forgot/reset password workflows.
- **In-App Issue & Feedback Reporter**: Direct submission of bug reports, UI issues, or feature requests with screenshot/video attachments (up to 20MB).

---

## 🏗️ Architecture & Technology Stack

```
                          ┌─────────────────────────┐
                          │   Frontend Application   │
                          │   (Next.js / React)     │
                          └────────────┬────────────┘
                                       │ HTTP / SSE / REST
                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                                 │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                            API Layer                                │  │
│  │   Auth  │  Goals  │  Subjects  │  Topics  │  Subtopics  │  Questions   │  │
│  │ Mistakes│ Revision│ Campaigns  │    AI    │  Accounts   │  Issues     │  │
│  └──────────────────────────────────┬──────────────────────────────────┘  │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                          Service Layer                              │  │
│  │  - RevisionEngine (SM-2, Urgency, Penalties, Streaks)               │  │
│  │  - CampaignEngine (Interleaving, Scheduling, Scope Resolution)      │  │
│  │  - AIService (Streaming, Prompt Hierarchy, Rate Limits)             │  │
│  │  - Auth & Account Services (JWT, OAuth, Quotas)                     │  │
│  └──────────────────────────────────┬──────────────────────────────────┘  │
│                                     ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        Repository Layer                             │  │
│  │  Async SQLAlchemy 2.0 Queries & Data Mappings                       │  │
│  └──────────────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────────────┼─────────────────────────────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            ▼                         ▼                         ▼
   ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
   │   PostgreSQL    │       │   Local Disk    │       │  LLM Providers  │
   │   (asyncpg)     │       │  File Uploads   │       │ OpenAI/Claude/  │
   │ Database Engine │       │ (PDFs, Images)  │       │     Gemini      │
   └─────────────────┘       └─────────────────┘       └─────────────────┘
```

| Layer | Technology |
|---|---|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Async, Python 3.12+) |
| **Database** | [PostgreSQL](https://www.postgresql.org/) |
| **ORM** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (`asyncpg` async driver) |
| **Migrations** | [Alembic](https://alembic.sqlalchemy.org/) |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) & `pydantic-settings` |
| **Security** | `python-jose` (JWT), `bcrypt` |
| **AI Providers** | `openai`, `anthropic`, `google-genai` |
| **File Storage** | Asynchronous local multipart storage with MIME verification |
| **Containerization** | Docker |

---

## 📁 Project Structure

```bash
backend/
├── alembic/                    # Database migration scripts and versions
│   ├── versions/               # Incremental schema migration files
│   └── env.py                  # Alembic async migration configuration
├── app/
│   ├── api/
│   │   ├── dependencies/       # Dependency injection (Auth, Services, DB)
│   │   └── routes/             # API route endpoints
│   │       ├── auth.py         # Login, register, OAuth, password reset
│   │       ├── goal.py         # Goal management
│   │       ├── subject.py      # Subject management
│   │       ├── topic.py        # Topic management
│   │       ├── subtopic.py     # Subtopics, notes, whiteboards & files
│   │       ├── question.py     # Practice question bank
│   │       ├── mistake.py      # Mistake notebook
│   │       ├── revision.py     # Spaced repetition queue & calendar
│   │       ├── campaign.py     # Revision campaigns & schedule generator
│   │       ├── ai.py           # Streaming AI study assistant
│   │       ├── account.py      # User account settings & plans
│   │       ├── issue.py        # Feedback & bug reporter
│   │       └── health.py       # Health checks
│   ├── core/
│   │   ├── config.py           # Pydantic Settings & environment variables
│   │   ├── logger.py           # Centralized logging configuration
│   │   └── timezone.py         # Timezone-aware date calculations
│   ├── db/
│   │   └── database.py         # Async engine & sessionmaker setup
│   ├── exceptions/             # Custom domain exceptions & global handlers
│   ├── models/                 # SQLAlchemy ORM database models
│   │   ├── enum.py             # Enums (Mastery, QuestionType, MistakeType, etc.)
│   │   ├── user.py             # User model
│   │   ├── account.py          # Account model (AI quota, plans)
│   │   ├── goal.py             # Goal model
│   │   ├── subject.py          # Subject model
│   │   ├── topic.py            # Topic model
│   │   ├── subtopic.py         # Subtopic model (notes, metrics, weightage)
│   │   ├── subtopic_file.py    # Subtopic uploaded documents
│   │   ├── subtopic_folder.py  # Nested file folders
│   │   ├── sketch_board.py     # Vector whiteboard canvases
│   │   ├── question.py         # Question model
│   │   ├── question_option.py  # Question options
│   │   ├── mistake.py          # Mistake notebook model
│   │   ├── revision_schedule.py# SM-2 revision schedule parameters
│   │   ├── revision_log.py     # Revision history event logs
│   │   ├── user_revision_settings.py # User streaks, limits & vacation
│   │   ├── campaign.py         # Revision campaign headers
│   │   ├── campaign_scope.py   # Scoped subjects & topics
│   │   ├── campaign_item.py    # Individual daily scheduled items
│   │   └── issue.py            # User reported issues with attachments
│   ├── repositories/           # Database access layer (CRUD operations)
│   ├── schema/                 # Pydantic request and response schemas
│   ├── services/               # Core business logic layer
│   │   ├── ai/                 # AI provider implementations & prompts
│   │   ├── revision_service.py # Spaced repetition algorithms & queues
│   │   ├── campaign_service.py # Revision sprint generator & interleaver
│   │   └── ...                 # Auth, Subtopic, Question, Mistake services
│   ├── utils/                  # Helper utilities (security, tokens)
│   └── main.py                 # FastAPI application factory & middleware
├── uploads/                    # Local storage for uploaded files and media
├── .env.example                # Example environment variables
├── alembic.ini                 # Alembic configuration file
├── Dockerfile                  # Container definition
└── pyproject.toml              # Dependencies and project metadata
```

---

## 🚦 Getting Started

### Prerequisites
- **Python 3.12+**
- **PostgreSQL 14+**
- Package manager: [`uv`](https://docs.astral.sh/uv/) (recommended) or `pip`

---

### 1. Clone & Setup Environment

```bash
cd learning-os/backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies using pip
pip install -e .

# Or using uv (faster)
uv sync
```

---

### 2. Configure Environment Variables

Copy the example `.env` file and customize your settings:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
APP_NAME=Learning OS
DEBUG=True
APP_HOST=0.0.0.0
APP_PORT=8000

# PostgreSQL Connection
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/learning_os

# Authentication & Security
JWT_SECRET=super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
CORS_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback

# AI Provider Configuration (openai | anthropic | gemini)
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Or for Anthropic:
# AI_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your-anthropic-api-key
# ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Or for Google Gemini:
# AI_PROVIDER=gemini
# GEMINI_API_KEY=your-gemini-api-key
# GEMINI_MODEL=gemini-2.0-flash

# Timezone for streaks and day boundaries
TIMEZONE=Asia/Kolkata
```

---

### 3. Run Database Migrations

Apply existing Alembic migrations to set up your PostgreSQL schema:

```bash
alembic upgrade head
```

> 💡 *Refer to [ALEMBIC_GUIDE.md](file:///Users/ashutosh/Documents/All%20in%20One/learning-os/backend/ALEMBIC_GUIDE.md) for how to generate and apply new schema revisions.*

---

### 4. Start the Application

#### Development Mode (with auto-reload):
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **Base URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc API Documentation**: `http://localhost:8000/redoc`

---

### 5. Running with Docker

You can also build and run using Docker:

```bash
# Build the image
docker build -t learning-os-backend .

# Run the container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name learning-os-api \
  learning-os-backend
```

---

## 📡 API Overview

All primary endpoints are prefixed with `/api/v1` (except `/health`):

| Module | Route Prefix | Key Functionality |
|---|---|---|
| **Health** | `GET /health` | Service liveness and readiness probe |
| **Auth** | `/api/v1/auth` | User registration, login, Google OAuth, password reset, token validation |
| **Users** | `/api/v1/users` | Profile retrieval and updates |
| **Account** | `/api/v1/account` | Plan details, AI token quotas, and usage counters |
| **Goals** | `/api/v1/users/{user_id}/goals` | CRUD operations and archiving for target exam goals |
| **Subjects** | `/api/v1/goals/{goal_id}/subjects` | Subject management and custom reordering |
| **Topics** | `/api/v1/subjects/{subject_id}/topics` | Topic management and sequencing |
| **Subtopics** | `/api/v1/topics/{topic_id}/subtopics` | Notes editor, whiteboard saves, file/folder uploads, metrics |
| **Questions** | `/api/v1/subtopics/{subtopic_id}/questions`<br>`/api/v1/goals/{goal_id}/questions` | Question bank, MCQ options, PYQ flags, scoring, and reordering |
| **Mistakes** | `/api/v1/subtopics/{subtopic_id}/mistakes`<br>`/api/v1/goals/{goal_id}/mistakes` | Error notebook, classifications, resolutions, and post-mortems |
| **Revisions** | `/api/v1/revisions` & `/api/v1/goals/{goal_id}/revisions` | SM-2 daily revision queue, review completion, calendar, and heatmaps |
| **Campaigns** | `/api/v1/campaigns` | Revision sprint creation, schedule previews, and daily tracking |
| **AI Tutor** | `/api/v1/ai/help` | Server-Sent Events (SSE) streaming contextual study assistant |
| **Issues** | `/api/v1/issues` | Bug reporting and feature requests with media attachments |

---

## 🧪 Development & Testing

Run tests with `pytest`:

```bash
# Run test suite
pytest

# Run tests with output
pytest -v -s
```

---

## 📜 License

This project is licensed under the MIT License — see the repository license details for more information.

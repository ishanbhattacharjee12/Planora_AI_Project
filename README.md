# Planora AI — Intelligent Project Planning & Orchestration Platform

![Planora AI Banner](frontend/public/randomtrees-logo-light.png)

**Planora AI** is an enterprise-grade AI-powered project intelligence and orchestration platform. It transforms unstructured project requirements, PRDs, and documentation into fully structured execution plans, granular task breakdowns, tech-stack alignments, semantic project memories, and optimal team resource assignments.

---

## 🌟 Key Features

### 1. 🤖 AI-Driven Project Decomposition & Planning
- **Automated Analysis**: Leverages Google Gemini models via an OpenAI-compatible gateway to analyze project scope, identify technical risks, suggest architecture patterns, and estimate delivery timelines.
- **Granular Task Generation**: Automatically extracts structured epics, user stories, acceptance criteria, and task dependencies from raw requirement documents.
- **Version Control & Plan Diffs**: Track modifications across project iterations with full version history and visual diff comparisons.

### 2. ⚡ Dual-Mode Orchestration Engine
- **Deterministic Workflow Pipeline**: A fast, reliable sequential pipeline for standard project decomposition, requirement extraction, and task mapping.
- **Multi-Agent LangGraph Orchestrator**: An autonomous multi-agent state graph where specialized agents (Architect, Risk Analyst, Project Manager, Resource Allocator) collaborate and refine project plans.

### 3. 🧠 Durable Semantic Project Memory & RAG
- **ChromaDB Vector Store**: Automatically embeds and indexes past projects and requirement chunks.
- **Cross-Project Intelligence**: Detects similarities with historical projects to reuse architectures, surface recurring risks, and recommend tested technology combinations.
- **Document Chunk Search**: Upload PDF, DOCX, and TXT specifications with semantic vector search and context-grounded answers.

### 4. 👥 Intelligent Team Recommendation & Capacity Allocation
- **Skill-Based Matching**: Matches employee skills against required project competencies using weighted scoring algorithms.
- **Workload & Capacity Tracking**: Prevents burnout by factoring in current allocations and real-time availability across sprints.

### 5. 🛡️ Enterprise Security & Data Governance
- **Zero-Trust Sensitive Data Guardrails**: Real-time scanning and blocking/redacting of PII, credentials, API keys, and connection strings before prompts reach the LLM.
- **Role-Based Access Control (RBAC)**: Fine-grained permissions across `Admin`, `Manager`, and `Employee` roles.
- **Complete Audit Trail**: Immutable logging of all user activities, document uploads, plan modifications, and AI interactions.

### 6. 📊 Observability, Analytics & Export
- **Langfuse Tracing**: End-to-end telemetry for AI calls, latency metrics, token consumption, and trace inspection.
- **Token Usage Bar**: Real-time token monitoring and cost tracking across analysis steps.
- **Executive PDF Reports**: Generates downloadable PDF summaries with project architecture, timelines, risk matrices, and task breakdowns via ReportLab.

---

## 🏗️ Architecture & Technology Stack

```
 Planora AI Platform
 ├── Frontend (React 18 + TypeScript + Vite)
 │   ├── Tailwind CSS / Modern Glassmorphic UI
 │   ├── Recharts & Interactive Kanban Board
 │   └── Role-based Dashboards (Admin / Manager / Employee)
 │
 ├── Backend (FastAPI + Async Python 3.11+)
 │   ├── LangGraph / Workflow Orchestration
 │   ├── Google Gemini API Gateway (OpenAI-Compatible)
 │   ├── SQLAlchemy Async ORM (SQLite / PostgreSQL + pgvector)
 │   ├── ChromaDB Semantic Memory & Embeddings
 │   ├── ReportLab PDF Generation
 │   └── JWT Auth & RBAC Middleware
 │
 └── Infrastructure
     ├── Docker & Docker Compose
     ├── PostgreSQL 16 + pgvector (Vector Database)
     └── Redis 7 (Caching & Message Broker)
```

| Layer | Technologies |
| :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Pydantic v2](https://docs.pydantic.dev/) |
| **AI & Orchestration** | [Google Gemini](https://ai.google.dev/), [LangGraph](https://github.com/langchain-ai/langgraph), [Langfuse](https://langfuse.com/) |
| **Databases** | [PostgreSQL](https://www.postgresql.org/) with [pgvector](https://github.com/pgvector/pgvector), [SQLite](https://www.sqlite.org/) (Local Dev), [ChromaDB](https://www.trychroma.com/) |
| **Frontend Framework** | [React 18](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vitejs.dev/) |
| **UI & Styling** | Modern CSS / Tailwind CSS, [Lucide React](https://lucide.dev/), [Recharts](https://recharts.org/) |
| **Testing** | [Pytest](https://docs.pytest.org/), [Playwright](https://playwright.dev/) (E2E) |

---

## 📁 Repository Structure

```text
.
├── backend/
│   ├── alembic/                # Database migrations (Alembic)
│   ├── app/
│   │   ├── ai/                 # Gemini gateway & PII / secret validators
│   │   ├── api/                # REST API routers (projects, tasks, auth, etc.)
│   │   ├── auth/               # JWT authentication & RBAC dependencies
│   │   ├── models/             # SQLAlchemy ORM database models
│   │   ├── orchestration/      # Workflow and LangGraph multi-agent systems
│   │   ├── rag/                # Document chunking & vector retrieval service
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── security/           # Data classification & privacy filters
│   │   ├── services/           # Business logic (matching, memory, PDF, etc.)
│   │   ├── config.py           # Application settings & environment config
│   │   ├── database.py         # Async database session & engine
│   │   └── main.py             # FastAPI entrypoint & middleware configuration
│   ├── scripts/                # Database seeding & validation utilities
│   ├── tests/                  # Pytest test suite (unit & integration)
│   ├── Dockerfile              # Backend container definition
│   ├── pytest.ini              # Pytest configuration
│   └── requirements.txt        # Python package dependencies
├── frontend/
│   ├── e2e/                    # Playwright end-to-end test suites
│   ├── public/                 # Static assets, manifests, and icons
│   ├── src/
│   │   ├── auth/               # AuthContext & ProtectedRoute components
│   │   ├── components/         # Reusable UI components (Kanban, Chat, etc.)
│   │   ├── constants/          # Tech stack metadata & constants
│   │   ├── pages/              # Pages for Admin, Manager, and Employee
│   │   ├── api.ts              # Centralized Axios API client
│   │   ├── App.tsx             # Application router
│   │   ├── main.tsx            # React root mount
│   │   └── index.css           # Global design system & utilities
│   ├── Dockerfile              # Frontend container definition
│   ├── package.json            # Node.js dependencies and scripts
│   ├── tsconfig.json           # TypeScript configuration
│   └── vite.config.ts          # Vite build & development server config
├── docker-compose.yml          # Multi-container orchestration
├── start-backend.ps1           # Quickstart script for backend (PowerShell)
├── start-frontend.ps1          # Quickstart script for frontend (PowerShell)
├── .env.example                # Example environment configuration template
└── .gitignore                  # Git exclusion rules
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher (with npm)
- **Docker & Docker Compose** (Optional, for containerized execution)

---

### Option A: Local Development Setup

#### 1. Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Update your `.env` with your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

#### 2. Start the Backend
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Seed demo database with initial users and skills
python scripts/seed.py

# Launch FastAPI server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend will be available at: **`http://localhost:8000`**  
Interactive API Docs (Swagger): **`http://localhost:8000/docs`**

#### 3. Start the Frontend
In a new terminal window:
```bash
# Navigate to frontend directory
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
Frontend will be available at: **`http://localhost:5173`**

---

### Option B: Docker Compose Setup

Run the entire platform (PostgreSQL + pgvector, Redis, Backend, and Frontend) with a single command:

```bash
docker compose up --build
```

---

## 🔐 Default Demo Accounts

The `scripts/seed.py` script provisions demo accounts for testing all role capabilities:

| Role | Email | Password | Access / Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@planora.local` | `admin123` | System audit logs, user management, global configuration |
| **Manager** | `manager1@planora.local` | `manager123` | Project creation, AI plan generation, team recommendations, Gantt/Kanban |
| **Employee** | `alice@planora.local` | `employee123` | Task tracking, personal dashboard, assignment status updates |

---

## ⚙️ Environment Configuration

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./projectintel.db` | Async database connection string (SQLite for dev, PostgreSQL for prod) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis cache and message queue connection URL |
| `JWT_SECRET` | `change-me-in-production...` | Secret key for signing JWT tokens |
| `JWT_ACCESS_EXPIRE_MINUTES` | `30` | JWT token validity window |
| `GEMINI_API_KEY` | *(Required for AI)* | Google Gemini API key |
| `GEMINI_BASE_URL` | `https://generativelanguage...` | OpenAI-compatible endpoint for Google Gemini |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Gemini model name |
| `ORCHESTRATION_MODE` | `workflow` | Analysis engine mode: `workflow` or `agents` |
| `PROJECT_MEMORY_ENABLED` | `true` | Enables ChromaDB durable semantic memory |
| `CHROMA_PERSIST_PATH` | `./chroma_data` | Directory where ChromaDB vector data is stored |
| `LANGFUSE_PUBLIC_KEY` | *(Optional)* | Langfuse public key for LLM tracing |
| `LANGFUSE_SECRET_KEY` | *(Optional)* | Langfuse secret key for LLM tracing |
| `SENSITIVE_DATA_ACTION` | `block` | PII scanner behavior: `block` or `redact` |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins for CORS |

---

## 🧪 Testing & Validation

### Run Backend Unit & Integration Tests
```bash
cd backend
pytest tests/
```
The suite runs 39 automated tests covering authentication, AI gateway, sensitive data filtering, project memory, orchestration workflows, PDF generation, and API endpoints.

### Build and Test Frontend
```bash
cd frontend
# Check TypeScript types and bundle production assets
npm run build

# Run Playwright E2E tests
npx playwright test
```

---

## 📡 Core API Endpoints

- **Auth**: `/api/auth/login`, `/api/auth/me`, `/api/auth/refresh`
- **Projects**: `/api/projects` (CRUD, analyze, export PDF, versions, history)
- **Tasks**: `/api/tasks` (Kanban management, assignment, status transitions)
- **Employees**: `/api/employees` (Skill matrix, department grouping, availability)
- **Documents**: `/api/documents` (Upload, chunking, RAG similarity search)
- **Admin**: `/api/admin/users`, `/api/admin/audit-logs`, `/api/admin/stats`
- **Health**: `/api/health`

---

## 📄 License

This project is licensed under the MIT License.

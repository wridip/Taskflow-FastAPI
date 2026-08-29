# 🚀 TaskFlow Enterprise API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20Async-red.svg?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063.svg?style=flat&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Pytest](https://img.shields.io/badge/Tests-22%20Passed-brightgreen.svg?style=flat&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

> **A production-ready Enterprise Task & Project Collaboration API** designed with **Clean Layered Architecture**, **Async SQLAlchemy 2.0**, **Pydantic v2**, **Role-Based Access Control (RBAC)**, **JWT Authentication with Refresh Tokens**, **Automated Audit Logging**, and **Background Notifications**.

---

## 📑 Table of Contents
- [Architecture & Design](#-architecture--design)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Directory Layout](#-project-directory-layout)
- [Quick Start Guide](#-quick-start-guide)
  - [Option A: Local Setup (Zero-config SQLite)](#option-a-local-setup)
  - [Option B: Docker Compose (PostgreSQL + Adminer)](#option-b-docker-compose)
- [API Documentation & Interactive Swagger](#-api-documentation--interactive-swagger)
- [Running Automated Tests](#-running-automated-tests)
- [Interview Talking Points & Technical Deep-Dive](#-interview-talking-points--technical-deep-dive)

---

## 🏛 Architecture & Design

TaskFlow is structured using **Clean Layered Architecture** with strict Separation of Concerns (SoC) and the **Repository Pattern**:

```
                              ┌────────────────────────────────────────┐
                              │           FastAPI Client (HTTP)        │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │       API Routers / Controllers        │
                              │      (app/api/v1/*.py)                 │
                              │  - Request validation via Pydantic v2  │
                              │  - Auth & Dependency Injection         │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │            Services Layer              │
                              │      (app/services/*.py)               │
                              │  - Business logic & domain rules       │
                              │  - RBAC & permission checking          │
                              │  - Audit log triggers                  │
                              │  - Background worker tasks             │
                              └───────────┬────────────────┬───────────┘
                                          │                │
                        ┌─────────────────┘                └─────────────────┐
                        ▼                                                    ▼
    ┌────────────────────────────────────────┐             ┌────────────────────────────────────┐
    │          Repositories Layer            │             │        Background Dispatcher       │
    │      (app/repositories/*.py)           │             │  (app/services/notification_*.py)  │
    │  - Pure SQL query building (SQLAlchemy)│             │  - Asynchronous email/webhooks     │
    │  - Dynamic filtering & pagination      │             └────────────────────────────────────┘
    │  - Data aggregations                   │
    └───────────────────┬────────────────────┘
                        │
                        ▼
    ┌────────────────────────────────────────┐
    │            Database Layer              │
    │  (Async SQLite / PostgreSQL 16)        │
    └────────────────────────────────────────┘
```

---

## 🌟 Key Features

1. **Authentication & Authorization**:
   - Secure password hashing with `bcrypt` (salted and compute-hardened).
   - Stateless JWT tokens (short-lived `access_token` + long-lived `refresh_token` flow).
   - OAuth2 Password Flow support with interactive Swagger UI `Authorize` button.
2. **Multi-Tenancy & Role-Based Access Control (RBAC)**:
   - Workspaces/Organizations with tiered membership: `OWNER`, `ADMIN`, `MEMBER`, `VIEWER`.
   - Strict hierarchical permission enforcement on projects, tasks, and member operations.
3. **Task & Project Management**:
   - Status transitions (`BACKLOG` -> `TODO` -> `IN_PROGRESS` -> `IN_REVIEW` -> `DONE`).
   - Priority levels (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), due date tracking, estimated hours, and tags.
   - Task comments with author relationships and chronological history.
4. **Dynamic Search, Filtering & Standardized Pagination**:
   - Multi-field search across titles, descriptions, and tags.
   - Filtering by status, priority, assignee ID, and due date range.
   - Dynamic sorting (`asc` / `desc` on any column) with standardized `PaginatedResponse[T]` metadata (`total_pages`, `has_next`, `has_previous`).
5. **Real-Time Workspace Analytics & Audit Trail**:
   - Aggregated metrics: Task completion rate (%), overdue task counter, status & priority breakdown.
   - Per-member workload tracker (assigned, completed, pending).
   - Automated immutable audit activity feed recording actions (`CREATED`, `UPDATED`, `STATUS_CHANGED`, `ASSIGNED`, `MEMBER_ADDED`, etc.).
6. **Asynchronous Background Tasks**:
   - Non-blocking task assignment and status update notifications using FastAPI `BackgroundTasks`.
7. **Database Migrations & Test Suite**:
   - Production migrations configured with Alembic (`alembic upgrade head`).
   - 22 comprehensive automated tests with in-memory isolated database fixtures (`pytest-asyncio` + `httpx`).

---

## 🛠 Tech Stack

| Component | Technology | Why Chosen for Production |
|---|---|---|
| **Web Framework** | **FastAPI** (v0.110+) | High performance (Starlette/Uvicorn), native `async/await`, automatic OpenAPI docs, and robust Dependency Injection. |
| **Data Validation** | **Pydantic v2** | 5x-10x faster validation written in Rust core (`pydantic-core`), strict type safety, automatic JSON Schema generation. |
| **ORM** | **SQLAlchemy 2.0 (Async)** | Industry standard Python ORM with full async IO support, preventing event loop blocking during DB calls. |
| **DB Migrations** | **Alembic** | Version-controlled, reproducible database schema migrations. |
| **Authentication** | **PyJWT + Bcrypt** | Secure stateless authentication, cryptographic signature verification, and standard password hashing. |
| **Testing** | **Pytest + pytest-asyncio + HTTPX** | Async test client simulating real HTTP requests against an isolated in-memory test database. |
| **Containerization**| **Docker + Docker Compose** | Multi-stage containerization with non-root security and PostgreSQL 16. |

---

## 📁 Project Directory Layout

```
FastAPI Project/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── Dockerfile                # Multi-stage production container definition
├── docker-compose.yml        # Multi-container orchestration (FastAPI + PostgreSQL + Adminer)
├── pyproject.toml            # Pytest & tool configurations
├── requirements.txt          # Production and development dependencies
├── alembic.ini               # Alembic configuration
├── alembic/                  # Database migration versions and environment
│   ├── env.py
│   └── versions/
│       └── 2026_08_27_..._initial_tables.py
├── scripts/
│   └── seed_data.py          # Demo dataset generator (Alex, Sarah, John)
├── app/
│   ├── main.py               # Application factory, lifespan, CORS, and middleware
│   ├── core/
│   │   ├── config.py         # Pydantic BaseSettings (env parsing)
│   │   ├── database.py       # Async SQLAlchemy engine, sessionmaker, Base
│   │   ├── security.py       # Bcrypt hashing & PyJWT token utilities
│   │   ├── exceptions.py     # Custom domain exceptions
│   │   ├── handlers.py       # Standardized JSON error response handlers
│   │   ├── middleware.py     # Request ID (X-Request-ID) & timing (X-Process-Time)
│   │   └── dependencies.py   # JWT user extraction & role verification
│   ├── models/               # SQLAlchemy 2.0 mapped models
│   │   ├── base.py           # TimestampMixin and Enums
│   │   ├── user.py           # User model
│   │   ├── workspace.py      # Workspace model
│   │   ├── workspace_member.py # Membership & Role association
│   │   ├── project.py        # Project model
│   │   ├── task.py           # Task model
│   │   ├── comment.py        # Task comments
│   │   └── activity_log.py   # Workspace audit logs
│   ├── schemas/              # Pydantic v2 validation DTOs
│   │   ├── common.py         # PaginatedResponse[T], PaginationMeta, HealthResponse
│   │   ├── token.py          # Token, RefreshTokenRequest, PasswordChangeRequest
│   │   ├── user.py           # UserCreate, UserLogin, UserProfileResponse
│   │   ├── workspace.py      # Workspace DTOs & Member management
│   │   ├── project.py        # Project DTOs
│   │   ├── task.py           # Task DTOs & FilterParams
│   │   ├── comment.py        # Comment DTOs
│   │   └── analytics.py      # Workspace analytics & Member workload
│   ├── repositories/         # Database query abstraction (Repository Pattern)
│   │   ├── base.py           # Generic BaseRepository[T]
│   │   ├── user_repo.py
│   │   ├── workspace_repo.py
│   │   ├── workspace_member_repo.py
│   │   ├── project_repo.py
│   │   ├── task_repo.py
│   │   ├── comment_repo.py
│   │   └── activity_repo.py
│   ├── services/             # Business Logic & Orchestration
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── workspace_service.py
│   │   ├── project_service.py
│   │   ├── task_service.py
│   │   ├── analytics_service.py
│   │   └── notification_service.py
│   └── api/
│       └── v1/               # Versioned RESTful route definitions
│           ├── router.py
│           ├── auth.py
│           ├── users.py
│           ├── workspaces.py
│           ├── projects.py
│           ├── tasks.py
│           └── analytics.py
└── tests/                    # Automated Test Suite (100% Pass)
    ├── conftest.py           # Test database session and client fixtures
    ├── test_auth.py
    ├── test_workspaces.py
    ├── test_projects.py
    ├── test_tasks.py
    └── test_analytics.py
```

---

## ⚡ Quick Start Guide

### Option A: Local Setup (Zero-config SQLite)

1. **Activate Virtual Environment & Install Dependencies**:
   ```bash
   # Windows PowerShell:
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Seed Demo Data (Users, Projects, Tasks)**:
   ```bash
   python scripts/seed_data.py
   ```

4. **Start Development Server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Open **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Open **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option B: Docker Compose (PostgreSQL + Adminer)

Run the full production stack with one command:
```bash
docker-compose up --build
```
- **API Server**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Adminer DB Client**: [http://localhost:8080](http://localhost:8080) (System: PostgreSQL, Server: `db`, User: `postgres`, Pass: `postgres`, DB: `taskflow_db`)

---

## 🔑 Demo Credentials (from Seed Data)

| Role | Email | Password | Privileges |
|---|---|---|---|
| **Owner** | `alex@taskflow.dev` | `Password123!` | Full workspace administration, member role transfers, workspace deletion |
| **Admin** | `sarah@taskflow.dev` | `Password123!` | Project & task management, member invites & updates |
| **Member** | `john@taskflow.dev` | `Password123!` | Task creation, status updates, commenting |

---

## 🧪 Running Automated Tests

Run the full pytest suite with verbose output and test coverage report:
```bash
pytest -v --cov=app --cov-report=term-missing
```

Output:
```text
============================= test session starts =============================
collected 22 items

tests/test_analytics.py::test_workspace_analytics PASSED                 [  4%]
tests/test_analytics.py::test_workspace_activity_feed PASSED             [  9%]
tests/test_auth.py::test_register_user_success PASSED                    [ 13%]
tests/test_auth.py::test_register_duplicate_email_fails PASSED           [ 18%]
tests/test_auth.py::test_login_success PASSED                            [ 22%]
tests/test_auth.py::test_login_invalid_password_fails PASSED             [ 27%]
tests/test_auth.py::test_refresh_token_flow PASSED                       [ 31%]
tests/test_auth.py::test_get_user_profile PASSED                         [ 36%]
tests/test_auth.py::test_update_profile PASSED                           [ 40%]
tests/test_auth.py::test_change_password PASSED                          [ 45%]
tests/test_projects.py::test_create_project_in_workspace PASSED          [ 50%]
tests/test_projects.py::test_list_projects_in_workspace PASSED           [ 54%]
tests/test_projects.py::test_get_and_update_project PASSED               [ 59%]
tests/test_tasks.py::test_create_and_get_task PASSED                     [ 63%]
tests/test_tasks.py::test_filter_and_search_tasks PASSED                 [ 68%]
tests/test_tasks.py::test_update_task_status PASSED                      [ 72%]
tests/test_tasks.py::test_comments_on_task PASSED                        [ 77%]
tests/test_workspaces.py::test_create_workspace PASSED                   [ 81%]
tests/test_workspaces.py::test_create_workspace_duplicate_slug_fails PASSED [ 86%]
tests/test_workspaces.py::test_list_user_workspaces PASSED               [ 90%]
tests/test_workspaces.py::test_get_workspace_details PASSED              [ 95%]
tests/test_workspaces.py::test_add_and_update_workspace_member PASSED    [100%]

============================= 22 passed in 12.90s =============================
```

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).

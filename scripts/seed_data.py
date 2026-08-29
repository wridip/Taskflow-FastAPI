import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.models.activity_log import ActivityLog
from app.models.base import ActivityAction, TaskPriority, TaskStatus, WorkspaceRole
from app.models.comment import Comment
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember


async def seed() -> None:
    print("[*] Seeding TaskFlow demo data...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        existing_users = await session.execute(select(User))
        if existing_users.scalars().first():
            print("[!] Database already contains users. Skipping seed.")
            return

        now = datetime.now(timezone.utc)

        # 1. Create Users
        alex = User(
            email="alex@taskflow.dev",
            full_name="Alex Rivera",
            hashed_password=hash_password("Password123!"),
            is_active=True,
            is_superuser=True,
        )
        sarah = User(
            email="sarah@taskflow.dev",
            full_name="Sarah Chen",
            hashed_password=hash_password("Password123!"),
            is_active=True,
            is_superuser=False,
        )
        john = User(
            email="john@taskflow.dev",
            full_name="John Doe",
            hashed_password=hash_password("Password123!"),
            is_active=True,
            is_superuser=False,
        )
        session.add_all([alex, sarah, john])
        await session.flush()
        print("[+] Created demo users (alex@taskflow.dev, sarah@taskflow.dev, john@taskflow.dev)")

        # 2. Create Workspace
        workspace = Workspace(
            name="FinTech Engineering",
            slug="fintech-engineering",
            description="Core engineering workspace for high-scale payment systems.",
            owner_id=alex.id,
        )
        session.add(workspace)
        await session.flush()

        # 3. Add Members
        m1 = WorkspaceMember(workspace_id=workspace.id, user_id=alex.id, role=WorkspaceRole.OWNER)
        m2 = WorkspaceMember(workspace_id=workspace.id, user_id=sarah.id, role=WorkspaceRole.ADMIN)
        m3 = WorkspaceMember(workspace_id=workspace.id, user_id=john.id, role=WorkspaceRole.MEMBER)
        session.add_all([m1, m2, m3])
        await session.flush()
        print("[+] Created workspace 'FinTech Engineering' with 3 members")

        # 4. Create Projects
        proj_payments = Project(
            workspace_id=workspace.id,
            name="Payment Gateway Service",
            description="High-throughput payment processing engine with idempotency & webhooks.",
            created_by_id=alex.id,
        )
        proj_dashboard = Project(
            workspace_id=workspace.id,
            name="Merchant Analytics Dashboard",
            description="React & FastAPI analytics dashboard for merchant transaction reports.",
            created_by_id=sarah.id,
        )
        session.add_all([proj_payments, proj_dashboard])
        await session.flush()
        print("[+] Created demo projects")

        # 5. Create Tasks
        tasks = [
            Task(
                project_id=proj_payments.id,
                title="Design Stripe Webhook Idempotency Layer",
                description="Use Redis distributed lock + unique payload hash to prevent duplicate payouts.",
                status=TaskStatus.DONE,
                priority=TaskPriority.URGENT,
                due_date=now - timedelta(days=2),
                estimated_hours=6.0,
                assignee_id=sarah.id,
                reporter_id=alex.id,
                tags="payments,security,redis",
            ),
            Task(
                project_id=proj_payments.id,
                title="Implement Rate Limiting Middleware",
                description="Token-bucket rate limiter per API key using Redis sliding window.",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                due_date=now + timedelta(days=3),
                estimated_hours=4.5,
                assignee_id=sarah.id,
                reporter_id=alex.id,
                tags="security,middleware,rate-limiting",
            ),
            Task(
                project_id=proj_payments.id,
                title="Audit Database Indexes for Transaction Logs",
                description="Review compound indexes on (merchant_id, created_at, status) for latency reduction.",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                due_date=now + timedelta(days=7),
                estimated_hours=3.0,
                assignee_id=john.id,
                reporter_id=sarah.id,
                tags="database,optimization,postgres",
            ),
            Task(
                project_id=proj_dashboard.id,
                title="Build Real-Time Revenue Chart Component",
                description="Streaming WebSocket data into Chart.js for real-time sales visualization.",
                status=TaskStatus.IN_REVIEW,
                priority=TaskPriority.HIGH,
                due_date=now + timedelta(days=1),
                estimated_hours=8.0,
                assignee_id=john.id,
                reporter_id=sarah.id,
                tags="frontend,charts,websocket",
            ),
            Task(
                project_id=proj_dashboard.id,
                title="Export Monthly Financial Statement CSV",
                description="Background worker task to stream 100k+ transaction rows into CSV report.",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                due_date=now + timedelta(days=5),
                estimated_hours=5.0,
                assignee_id=alex.id,
                reporter_id=sarah.id,
                tags="reports,csv,celery",
            ),
        ]
        session.add_all(tasks)
        await session.flush()
        print(f"[+] Created {len(tasks)} demo tasks across projects")

        # 6. Add Comments
        c1 = Comment(
            task_id=tasks[0].id,
            author_id=alex.id,
            content="Great job on the idempotency lock implementation! Passing all stress tests.",
        )
        c2 = Comment(
            task_id=tasks[1].id,
            author_id=sarah.id,
            content="Working on unit tests for Redis token bucket right now. Should be ready for review tomorrow.",
        )
        session.add_all([c1, c2])
        await session.flush()

        # 7. Add Activity Logs
        logs = [
            ActivityLog(
                workspace_id=workspace.id,
                actor_id=alex.id,
                action=ActivityAction.CREATED,
                entity_type="WORKSPACE",
                entity_id=workspace.id,
                details='{"name": "FinTech Engineering"}',
            ),
            ActivityLog(
                workspace_id=workspace.id,
                actor_id=sarah.id,
                action=ActivityAction.STATUS_CHANGED,
                entity_type="TASK",
                entity_id=tasks[0].id,
                details='{"old_status": "IN_REVIEW", "new_status": "DONE"}',
            ),
        ]
        session.add_all(logs)
        await session.commit()
        print("[+] Created demo comments and activity logs")

    print("\n[SUCCESS] Seeding complete! Demo credentials:")
    print("   -> Alex (Owner):  email='alex@taskflow.dev'   password='Password123!'")
    print("   -> Sarah (Admin): email='sarah@taskflow.dev'  password='Password123!'")
    print("   -> John (Member): email='john@taskflow.dev'   password='Password123!'")


if __name__ == "__main__":
    asyncio.run(seed())

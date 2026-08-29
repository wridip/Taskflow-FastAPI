import logging
from typing import Optional

logger = logging.getLogger("taskflow.notifications")


class NotificationService:
    @staticmethod
    async def send_task_assigned_notification(
        assignee_email: str,
        assignee_name: str,
        task_title: str,
        task_id: int,
        project_name: str,
    ) -> None:
        """Simulate async email/webhook notification for task assignment."""
        logger.info(
            f"[Notification] Task #{task_id} ('{task_title}') in project '{project_name}' "
            f"assigned to {assignee_name} <{assignee_email}>."
        )

    @staticmethod
    async def send_status_changed_notification(
        reporter_email: Optional[str],
        task_title: str,
        task_id: int,
        old_status: str,
        new_status: str,
        updated_by_name: str,
    ) -> None:
        """Simulate async email/webhook notification for task status change."""
        if reporter_email:
            logger.info(
                f"[Notification] Task #{task_id} ('{task_title}') status changed "
                f"from {old_status} to {new_status} by {updated_by_name}. Notified {reporter_email}."
            )

"""Outbound notifications for the Workflow Agent: email, push, SMS.
All sends are recorded in Firestore for the audit trail; demo mode logs only."""
from app.core.config import settings
from app.core.logging import get_logger
from app.services.firestore_db import fs

log = get_logger(__name__)


class NotificationService:
    def notify(self, channel: str, recipient: str, subject: str, body: str,
               incident_id: str | None = None) -> str:
        """channel: email | push | sms. Returns notification doc id."""
        record = {
            "channel": channel, "recipient": recipient, "subject": subject,
            "body": body, "incident_id": incident_id,
            "status": "sent" if settings.DEMO_MODE else "queued",
        }
        doc_id = fs.add("notifications", record)
        log.info("notification_sent", channel=channel, recipient=recipient,
                 subject=subject, doc_id=doc_id)
        # Production: hand off to SendGrid / FCM / Twilio via Pub/Sub push subscriber.
        return doc_id

    def broadcast_citizens(self, zone: str, message: str, incident_id: str | None = None) -> str:
        return self.notify("push", f"citizens:{zone}", "Emergency Advisory", message, incident_id)


notifier = NotificationService()

"""Connector registry. Maps a stable name to its Connector class.

Names match the M10 issues and the dispatcher/agent vocabulary. The runner walks
this registry; adding a source is adding one module and one entry here.
"""

from __future__ import annotations

from ..base import Connector
from .audit_feed import AuditFeed
from .churn_reasons import ChurnReasons
from .content_calendar import ContentCalendar
from .email_engagement import EmailEngagement
from .nps_feedback import NpsFeedback
from .support_tickets import SupportTickets
from .webinar_metrics import WebinarMetrics

REGISTRY: dict[str, type[Connector]] = {
    "email_engagement": EmailEngagement,
    "support_tickets": SupportTickets,
    "churn_reasons": ChurnReasons,
    "content_calendar": ContentCalendar,
    "webinar_metrics": WebinarMetrics,
    "nps_feedback": NpsFeedback,
    "audit_feed": AuditFeed,
}

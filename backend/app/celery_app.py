from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "netbill",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.billing", "app.tasks.update_checker", "app.tasks.bandwidth"],
)

celery.conf.beat_schedule = {
    "generate-monthly-invoices": {
        "task": "app.tasks.billing.generate_monthly_invoices_task",
        "schedule": crontab(day_of_month=str(settings.BILLING_GENERATE_DAY), hour="2", minute="0"),
    },
    "check-overdue-invoices": {
        "task": "app.tasks.billing.check_overdue_invoices_task",
        "schedule": crontab(hour="6", minute="0"),
    },
    "process-graduated-disconnect": {
        "task": "app.tasks.billing.process_graduated_disconnect_task",
        "schedule": crontab(hour="7", minute="0"),
    },
    "send-billing-reminders": {
        "task": "app.tasks.billing.send_billing_reminders_task",
        "schedule": crontab(hour="9", minute="0"),
    },
    "process-notifications": {
        "task": "app.tasks.billing.process_notifications_task",
        "schedule": 300.0,  # Every 5 minutes
    },
    "check-for-updates": {
        "task": "app.tasks.update_checker.check_updates_task",
        "schedule": crontab(hour="3", minute="30"),
    },
    "collect-bandwidth": {
        "task": "app.tasks.bandwidth.collect_bandwidth_task",
        "schedule": 900.0,
    },
    "check-data-caps": {
        "task": "app.tasks.bandwidth.check_data_caps_task",
        "schedule": crontab(hour="*/2", minute="15"),
    },
}

celery.conf.timezone = "Asia/Manila"

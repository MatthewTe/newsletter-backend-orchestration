from celery import shared_task

from apps.foreign_policy.models import ForeginPolicyRssFeed

# TODO: Refactor tasks to be classes:
# https://docs.celeryq.dev/en/latest/userguide/tasks.html
# https://stackoverflow.com/questions/41933814/how-to-pass-a-class-based-task-into-celery-beat-schedule

@shared_task()
def load_foreign_policy_rss_feed():
    """Triggers the ingestion process for downloading and parsing the FP RSS Feed"""
    new_rss_feed = ForeginPolicyRssFeed()
    new_rss_feed.save()
import asyncio
from datetime import timedelta
from celery import Celery
import json

from novig_bot import NovigSender
from process_manager import ProcessManager

celery_app = Celery(
    "notify_user_celery",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/1",
)

celery_app.conf.beat_schedule = {
    "send_notifications": {
        "task": "celery_notification.notify_user",
        "schedule": timedelta(seconds=30),
    },
}

async def run_notify():
    with open("nfl_filters.json", "r") as f:
        nfl_filters = json.load(f)
    with open("ncaaf_filters.json", "r") as f:
        ncaaf_filters = json.load(f)

    sender_nfl = NovigSender(filter_data=nfl_filters, difference_amount=3000)
    sender_ncaaf = NovigSender(filter_data=ncaaf_filters, difference_amount=4000)

    nfl_data, ncaaf_data = await asyncio.gather(
        sender_nfl.runner(),
        sender_ncaaf.runner()
    )

    nfl_manager = ProcessManager(redis_database=8, difference_amount=1500, league="NFL")
    ncaaf_manager = ProcessManager(redis_database=9, difference_amount=1500, league="NCAAF")

    nfl_manager.manger(nfl_data["NFL"], "NFL")
    ncaaf_manager.manger(ncaaf_data["NCAAF"], "NCAAF")

@celery_app.task(name="celery_notification.notify_user")
def notify_user():
    asyncio.run(run_notify())

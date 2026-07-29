"""
Application task schedule.

Register jobs/callbacks with the tamilPY scheduler.
Run due tasks via: ``tpy schedule run`` (typically every minute from cron).
"""


def register(scheduler) -> None:
    """
    Configure scheduled events.

    Example::

        scheduler.call(heartbeat).every_five_minutes().name("heartbeat")
        scheduler.job(SendDigest()).daily_at("08:00")
    """
    # scheduler.call(heartbeat).every_five_minutes().name("heartbeat")
    return None


def heartbeat() -> None:
    """Sample callback — replace or remove."""
    return None

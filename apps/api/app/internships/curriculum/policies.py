from datetime import datetime


def unit_is_released(*, now: datetime, release_at: datetime | None, week_start: datetime) -> bool:
    return now >= (release_at or week_start)


def week_is_unlocked(*, now: datetime, week_start: datetime, previous_complete: bool) -> bool:
    return now >= week_start and previous_complete

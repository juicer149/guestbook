from __future__ import annotations


MIN_GUEST_STAY_LENGTH_DAYS = 1
MAX_GUEST_STAY_LENGTH_DAYS = 14


def is_valid_guest_stay_length(days: int) -> bool:
    return (
        MIN_GUEST_STAY_LENGTH_DAYS
        <= days
        <= MAX_GUEST_STAY_LENGTH_DAYS
    )


def guest_stay_lengths() -> range:
    return range(
        MIN_GUEST_STAY_LENGTH_DAYS,
        MAX_GUEST_STAY_LENGTH_DAYS + 1,
    )

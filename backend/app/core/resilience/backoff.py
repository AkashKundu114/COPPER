"""Exponential Backoff and Jitter Algorithms for Distributed Retries."""

import random


def calculate_backoff(
    attempt: int,
    base_delay_s: float = 0.5,
    max_delay_s: float = 30.0,
    multiplier: float = 2.0,
    jitter: bool = True,
) -> float:
    """Calculates exponential backoff delay with full jitter (Equal or Full Jitter).

    Formula (Full Jitter):
        temp = min(max_delay, base_delay * (multiplier ** attempt))
        sleep = random.uniform(0, temp)
    """
    if attempt < 0:
        return 0.0

    calculated = base_delay_s * (multiplier**attempt)
    capped = min(max_delay_s, calculated)

    if not jitter:
        return capped

    # Full jitter distributes load uniformly between 0 and capped delay
    return round(random.uniform(base_delay_s * 0.5, capped), 3)

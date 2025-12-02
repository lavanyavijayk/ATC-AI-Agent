import time


def millis() -> int:
    """Return current time in milliseconds since epoch."""
    return int(time.time() * 1000)

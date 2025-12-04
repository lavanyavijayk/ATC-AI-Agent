from __future__ import annotations
import threading
from typing import Dict


class SingletonMeta(type):
    """
    Thread-safe Singleton metaclass.
    Any class using this metaclass will be a singleton per Python process.
    """
    _instances: Dict[type, object] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        # Double-checked locking
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
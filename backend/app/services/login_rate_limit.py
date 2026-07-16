import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status


class LoginRateLimiter:
    def __init__(self, limit: int = 5, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.attempts: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self.lock:
            attempts = self.attempts[key]
            while attempts and now - attempts[0] >= self.window_seconds:
                attempts.popleft()
            if len(attempts) >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="登录尝试过于频繁，请稍后再试",
                    headers={"Retry-After": str(self.window_seconds)},
                )
            attempts.append(now)

    def reset(self, key: str) -> None:
        with self.lock:
            self.attempts.pop(key, None)


login_rate_limiter = LoginRateLimiter()


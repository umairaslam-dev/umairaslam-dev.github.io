from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 3
    base_delay_seconds: float = 0.05

    async def execute(self, operation: Callable[[], Awaitable[T]]) -> T:
        last_error: Exception | None = None
        for attempt in range(self.attempts):
            try:
                return await operation()
            except Exception as exc:  # policy boundary: retry only where explicitly used
                last_error = exc
                if attempt == self.attempts - 1:
                    break
                await asyncio.sleep(self.base_delay_seconds * (2 ** attempt))
        assert last_error is not None
        raise last_error

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from .models import TradeEvent


@dataclass
class InMemoryTradeRepository:
    """Thread-safe-enough for one asyncio event loop via a single lock."""

    _trades: dict[str, TradeEvent] = field(default_factory=dict)
    _processed_event_ids: set[str] = field(default_factory=set)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def already_processed(self, event_id: str) -> bool:
        async with self._lock:
            return event_id in self._processed_event_ids

    async def save_if_new(self, event: TradeEvent) -> bool:
        """Atomically applies the event once. Returns False for a duplicate."""
        async with self._lock:
            if event.event_id in self._processed_event_ids:
                return False
            self._trades[event.trade_id] = event
            self._processed_event_ids.add(event.event_id)
            return True

    async def get(self, trade_id: str) -> TradeEvent | None:
        async with self._lock:
            return self._trades.get(trade_id)

    async def all(self) -> dict[str, TradeEvent]:
        async with self._lock:
            return dict(self._trades)

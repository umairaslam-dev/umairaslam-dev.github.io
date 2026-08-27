from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from .models import TradeEvent, TradeState
from .repository import InMemoryTradeRepository
from .retry import RetryPolicy

Processor = Callable[[TradeEvent], Awaitable[TradeEvent]]


@dataclass
class EngineMetrics:
    accepted: int = 0
    duplicates: int = 0
    processed: int = 0
    failed: int = 0
    dlq: int = 0


@dataclass
class DistributedTradeEngine:
    repository: InMemoryTradeRepository
    max_concurrency: int = 32
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    metrics: EngineMetrics = field(default_factory=EngineMetrics)
    dead_letter_queue: list[tuple[TradeEvent, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._semaphore = asyncio.Semaphore(self.max_concurrency)

    async def process(self, event: TradeEvent) -> TradeEvent | None:
        self.metrics.accepted += 1
        if await self.repository.already_processed(event.event_id):
            self.metrics.duplicates += 1
            return None

        async with self._semaphore:
            try:
                settled = await self.retry_policy.execute(lambda: self._pipeline(event))
                persisted = await self.repository.save_if_new(settled)
                if not persisted:
                    self.metrics.duplicates += 1
                    return None
                self.metrics.processed += 1
                return settled
            except Exception as exc:
                self.metrics.failed += 1
                self.dead_letter_queue.append((event, str(exc)))
                self.metrics.dlq += 1
                return None

    async def process_batch(self, events: list[TradeEvent]) -> list[TradeEvent | None]:
        return await asyncio.gather(*(self.process(event) for event in events))

    async def _pipeline(self, event: TradeEvent) -> TradeEvent:
        validated = await self._validate(event)
        enriched = await self._enrich(validated)
        return await self._settle(enriched)

    async def _validate(self, event: TradeEvent) -> TradeEvent:
        if event.quantity <= 0:
            raise ValueError("quantity must be positive")
        if event.price <= 0:
            raise ValueError("price must be positive")
        await asyncio.sleep(0)
        return event.transition_to(TradeState.VALIDATED)

    async def _enrich(self, event: TradeEvent) -> TradeEvent:
        await asyncio.sleep(0)
        return event.transition_to(TradeState.ENRICHED)

    async def _settle(self, event: TradeEvent) -> TradeEvent:
        await asyncio.sleep(0)
        return event.transition_to(TradeState.SETTLED)

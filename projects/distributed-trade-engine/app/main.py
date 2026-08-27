from __future__ import annotations

import asyncio

from .engine import DistributedTradeEngine
from .models import TradeEvent
from .reconciliation import ReconciliationEngine
from .repository import InMemoryTradeRepository


def sample_events() -> list[TradeEvent]:
    return [
        TradeEvent(
            event_id=f"evt-{i}",
            trade_id=f"trade-{i}",
            account_id=f"acct-{i % 4}",
            instrument="SPY",
            quantity=100 + i,
            price=500.0 + i,
        )
        for i in range(100)
    ]


async def run() -> None:
    repository = InMemoryTradeRepository()
    engine = DistributedTradeEngine(repository=repository, max_concurrency=16)

    events = sample_events()
    await engine.process_batch(events)

    # Replay part of the stream to demonstrate idempotency.
    await engine.process_batch(events[:10])

    authoritative = await repository.all()
    reconciliation = await ReconciliationEngine(repository).compare(authoritative)

    print("processed:", engine.metrics.processed)
    print("duplicates:", engine.metrics.duplicates)
    print("dlq:", engine.metrics.dlq)
    print("reconciliation clean:", reconciliation.clean)


if __name__ == "__main__":
    asyncio.run(run())

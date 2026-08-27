from __future__ import annotations

from dataclasses import dataclass

from .models import TradeEvent
from .repository import InMemoryTradeRepository


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    missing_trade_ids: tuple[str, ...]
    stale_trade_ids: tuple[str, ...]
    unexpected_trade_ids: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not (self.missing_trade_ids or self.stale_trade_ids or self.unexpected_trade_ids)


class ReconciliationEngine:
    def __init__(self, repository: InMemoryTradeRepository) -> None:
        self.repository = repository

    async def compare(self, authoritative: dict[str, TradeEvent]) -> ReconciliationResult:
        current = await self.repository.all()

        expected_ids = set(authoritative)
        current_ids = set(current)

        missing = expected_ids - current_ids
        unexpected = current_ids - expected_ids
        common = expected_ids & current_ids

        stale = {
            trade_id
            for trade_id in common
            if current[trade_id].state != authoritative[trade_id].state
            or current[trade_id].quantity != authoritative[trade_id].quantity
            or current[trade_id].price != authoritative[trade_id].price
        }

        return ReconciliationResult(
            missing_trade_ids=tuple(sorted(missing)),
            stale_trade_ids=tuple(sorted(stale)),
            unexpected_trade_ids=tuple(sorted(unexpected)),
        )

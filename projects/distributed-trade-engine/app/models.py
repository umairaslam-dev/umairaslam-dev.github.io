from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import FrozenSet


class TradeState(str, Enum):
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    ENRICHED = "ENRICHED"
    SETTLED = "SETTLED"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS: dict[TradeState, FrozenSet[TradeState]] = {
    TradeState.RECEIVED: frozenset({TradeState.VALIDATED, TradeState.FAILED}),
    TradeState.VALIDATED: frozenset({TradeState.ENRICHED, TradeState.FAILED}),
    TradeState.ENRICHED: frozenset({TradeState.SETTLED, TradeState.FAILED}),
    TradeState.SETTLED: frozenset(),
    TradeState.FAILED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class TradeEvent:
    event_id: str
    trade_id: str
    account_id: str
    instrument: str
    quantity: int
    price: float
    state: TradeState = TradeState.RECEIVED
    occurred_at: datetime = datetime.now(timezone.utc)

    def transition_to(self, target: TradeState) -> "TradeEvent":
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"invalid transition: {self.state} -> {target}")
        return replace(self, state=target)

    @property
    def notional(self) -> float:
        return self.quantity * self.price

import unittest

from app.models import TradeEvent, TradeState
from app.reconciliation import ReconciliationEngine
from app.repository import InMemoryTradeRepository


class ReconciliationTests(unittest.IsolatedAsyncioTestCase):
    async def test_detects_missing_stale_and_unexpected_trades(self) -> None:
        repo = InMemoryTradeRepository()

        current_one = TradeEvent("e1", "t1", "a1", "SPY", 10, 500.0, TradeState.SETTLED)
        current_extra = TradeEvent("e2", "t-extra", "a1", "QQQ", 5, 400.0, TradeState.SETTLED)
        await repo.save_if_new(current_one)
        await repo.save_if_new(current_extra)

        authoritative = {
            "t1": TradeEvent("a1", "t1", "a1", "SPY", 11, 500.0, TradeState.SETTLED),
            "t-missing": TradeEvent("a2", "t-missing", "a2", "IWM", 7, 220.0, TradeState.SETTLED),
        }

        result = await ReconciliationEngine(repo).compare(authoritative)

        self.assertEqual(result.stale_trade_ids, ("t1",))
        self.assertEqual(result.missing_trade_ids, ("t-missing",))
        self.assertEqual(result.unexpected_trade_ids, ("t-extra",))
        self.assertFalse(result.clean)


if __name__ == "__main__":
    unittest.main()

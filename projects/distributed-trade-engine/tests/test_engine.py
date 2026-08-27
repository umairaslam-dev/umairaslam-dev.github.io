import unittest

from app.engine import DistributedTradeEngine
from app.models import TradeEvent, TradeState
from app.repository import InMemoryTradeRepository


class TradeEngineTests(unittest.IsolatedAsyncioTestCase):
    async def test_processes_trade_to_settled(self) -> None:
        repo = InMemoryTradeRepository()
        engine = DistributedTradeEngine(repo, max_concurrency=4)
        event = TradeEvent("e1", "t1", "a1", "SPY", 10, 500.0)

        result = await engine.process(event)

        self.assertIsNotNone(result)
        self.assertEqual(result.state, TradeState.SETTLED)
        self.assertEqual(engine.metrics.processed, 1)

    async def test_duplicate_event_is_not_reapplied(self) -> None:
        repo = InMemoryTradeRepository()
        engine = DistributedTradeEngine(repo)
        event = TradeEvent("e1", "t1", "a1", "SPY", 10, 500.0)

        await engine.process(event)
        result = await engine.process(event)

        self.assertIsNone(result)
        self.assertEqual(engine.metrics.processed, 1)
        self.assertEqual(engine.metrics.duplicates, 1)

    async def test_invalid_trade_goes_to_dlq(self) -> None:
        repo = InMemoryTradeRepository()
        engine = DistributedTradeEngine(repo)
        event = TradeEvent("e1", "t1", "a1", "SPY", 0, 500.0)

        result = await engine.process(event)

        self.assertIsNone(result)
        self.assertEqual(engine.metrics.dlq, 1)
        self.assertEqual(engine.metrics.failed, 1)


if __name__ == "__main__":
    unittest.main()

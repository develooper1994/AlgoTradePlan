from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.algotradeplan.audit.event_store import EventRecord, InMemoryEventStore
from src.algotradeplan.bus.inproc import InProcBus
from src.algotradeplan.config.loader import load_runtime_config


class FoundationModulesTest(unittest.TestCase):
    def test_event_store_filters_stream(self) -> None:
        store = InMemoryEventStore()
        store.append(EventRecord(stream="orders", event_type="created", payload={"id": 1}))
        store.append(EventRecord(stream="fills", event_type="partial", payload={"id": 1}))

        order_events = store.list_by_stream("orders")
        self.assertEqual(len(order_events), 1)
        self.assertEqual(order_events[0].event_type, "created")

    def test_inproc_bus_dispatches_to_subscriber(self) -> None:
        bus = InProcBus()
        received: list[dict[str, object]] = []
        bus.subscribe("orders", received.append)

        bus.publish("orders", {"id": "ord-1"})
        self.assertEqual(received, [{"id": "ord-1"}])

    def test_load_runtime_config_reads_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runtime.json"
            path.write_text(
                json.dumps(
                    {
                        "environment": "dev",
                        "strategy_id": "demo_strategy",
                        "risk_limit_daily_loss": 123.4,
                    }
                ),
                encoding="utf-8",
            )

            config = load_runtime_config(path)

        self.assertEqual(config.environment, "dev")
        self.assertEqual(config.strategy_id, "demo_strategy")
        self.assertEqual(config.risk_limit_daily_loss, 123.4)


if __name__ == "__main__":
    unittest.main()

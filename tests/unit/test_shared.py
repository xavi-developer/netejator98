"""Unit tests for shared primitives (Result, EventBus, Clock, MachineId, DomainError)."""

from datetime import datetime, timezone
import unittest

from netejator98.shared.clock import FrozenClock, SystemClock
from netejator98.shared.errors import DomainError, InvalidEmailError
from netejator98.shared.event_bus import DomainEvent, EventBus
from netejator98.shared.machine_id import MachineId
from netejator98.shared.result import Err, Ok


class SampleEvent(DomainEvent):
    user_name: str = "test_user"


class TestResultType(unittest.TestCase):
    def test_ok_behavior(self) -> None:
        res = Ok(42)
        self.assertTrue(res.is_ok())
        self.assertFalse(res.is_err())
        self.assertEqual(res.unwrap(), 42)
        self.assertEqual(res.unwrap_or(0), 42)

        mapped = res.map(lambda x: str(x * 2))
        self.assertTrue(mapped.is_ok())
        self.assertEqual(mapped.unwrap(), "84")

        bound = res.bind(lambda x: Ok(f"value_{x}"))
        self.assertEqual(bound.unwrap(), "value_42")

    def test_err_behavior(self) -> None:
        res = Err(InvalidEmailError("Bad email"))
        self.assertFalse(res.is_ok())
        self.assertTrue(res.is_err())
        self.assertEqual(res.unwrap_or(100), 100)
        self.assertEqual(res.unwrap_err().message, "Bad email")

        with self.assertRaises(ValueError):
            res.unwrap()

        mapped = res.map(lambda x: x * 2)
        self.assertTrue(mapped.is_err())

        mapped_err = res.map_err(lambda e: DomainError(f"Wrapped: {e.message}"))
        self.assertEqual(mapped_err.unwrap_err().message, "Wrapped: Bad email")


class TestEventBus(unittest.TestCase):
    def test_publish_and_subscribe(self) -> None:
        bus = EventBus()
        received: list[SampleEvent] = []

        bus.subscribe(SampleEvent, received.append)

        ev = SampleEvent()
        bus.publish(ev)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], ev)
        self.assertEqual(len(bus.recorded_events), 1)

    def test_clear_recorded(self) -> None:
        bus = EventBus()
        bus.publish(SampleEvent())
        self.assertEqual(len(bus.recorded_events), 1)
        bus.clear_recorded()
        self.assertEqual(len(bus.recorded_events), 0)


class TestClock(unittest.TestCase):
    def test_system_clock_returns_utc(self) -> None:
        clock = SystemClock()
        now = clock.now_utc()
        self.assertIsNotNone(now.tzinfo)
        self.assertEqual(now.tzinfo, timezone.utc)

    def test_frozen_clock_deterministic(self) -> None:
        dt = datetime(2026, 9, 16, 10, 0, 0, tzinfo=timezone.utc)
        clock = FrozenClock(dt)
        self.assertEqual(clock.now_utc(), dt)

        clock.advance_seconds(30)
        self.assertEqual(clock.now_utc(), datetime(2026, 9, 16, 10, 0, 30, tzinfo=timezone.utc))


class TestMachineId(unittest.TestCase):
    def test_valid_machine_id(self) -> None:
        mid = MachineId("station-01")
        self.assertEqual(str(mid), "station-01")

    def test_empty_machine_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            MachineId("   ")

    def test_machine_id_current(self) -> None:
        mid = MachineId.current()
        self.assertTrue(len(mid.value) > 0)


if __name__ == "__main__":
    unittest.main()


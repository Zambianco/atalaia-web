import unittest
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from datetime import timezone

MODULE_PATH = Path(__file__).with_name("worker.py")
SPEC = spec_from_file_location("worker_module", MODULE_PATH)
sys.modules.setdefault("psycopg", types.SimpleNamespace(connect=lambda **kwargs: None))
fake_mqtt = types.SimpleNamespace(
    Client=object,
    CallbackAPIVersion=types.SimpleNamespace(VERSION2=object()),
)
sys.modules.setdefault("paho", types.ModuleType("paho"))
sys.modules.setdefault("paho.mqtt", types.ModuleType("paho.mqtt"))
sys.modules.setdefault("paho.mqtt.client", fake_mqtt)
WORKER = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(WORKER)


class WorkerTelemetryTests(unittest.TestCase):
    def test_normalize_accepts_nullable_fields(self):
        payload = {
            "type": "telemetry",
            "id": "AA:BB:CC:DD:EE:FF",
            "name": "Gateway Caixa Dagua",
            "probeId": "11:22:33:44:55:66",
            "probeName": "Sonda Caixa",
            "readingId": "11:22:33:44:55:66@2026-06-06T23:10:15",
            "fw": "gateway-0.1.0",
            "seq": 42,
            "receivedPackets": 42,
            "lostPackets": 3,
            "timeSinceLastReceptionMs": None,
            "rssi": -87,
            "snr": 7.5,
            "timestamp": None,
            "timestampEpoch": None,
            "temperature": None,
        }

        normalized = WORKER.normalize_telemetry(payload)

        self.assertIsNone(normalized["timeSinceLastReceptionMs"])
        self.assertEqual(normalized["rssi"], -87)
        self.assertEqual(normalized["snr"], 7.5)
        self.assertIsNone(normalized["timestamp"])
        self.assertIsNone(normalized["timestampEpoch"])
        self.assertIsNone(normalized["temperature"])

    def test_parse_recorded_at_uses_payload_timestamp(self):
        payload = {"timestamp": "2026-06-06T23:10:15Z"}

        recorded_at = WORKER.parse_recorded_at(payload)

        self.assertEqual(recorded_at.tzinfo, timezone.utc)
        self.assertEqual(recorded_at.isoformat(), "2026-06-06T23:10:15+00:00")

    def test_normalize_rejects_negative_counter(self):
        payload = {
            "type": "telemetry",
            "id": "AA:BB:CC:DD:EE:FF",
            "name": "Gateway Caixa Dagua",
            "probeId": "11:22:33:44:55:66",
            "probeName": "Sonda Caixa",
            "readingId": "11:22:33:44:55:66@2026-06-06T23:10:15",
            "fw": "gateway-0.1.0",
            "seq": 42,
            "receivedPackets": 42,
            "lostPackets": -1,
            "timeSinceLastReceptionMs": 5987,
            "rssi": -87,
            "snr": 7.5,
            "timestamp": "2026-06-06T23:10:15",
            "timestampEpoch": 1780783815,
            "temperature": 24.37,
        }

        with self.assertRaisesRegex(ValueError, "lostPackets"):
            WORKER.normalize_telemetry(payload)

    def test_normalize_rejects_missing_rssi(self):
        payload = {
            "type": "telemetry",
            "id": "AA:BB:CC:DD:EE:FF",
            "name": "Gateway Caixa Dagua",
            "probeId": "11:22:33:44:55:66",
            "probeName": "Sonda Caixa",
            "readingId": "11:22:33:44:55:66@2026-06-06T23:10:15",
            "fw": "gateway-0.1.0",
            "seq": 42,
            "receivedPackets": 42,
            "lostPackets": 3,
            "timeSinceLastReceptionMs": 5987,
            "snr": 7.5,
            "timestamp": "2026-06-06T23:10:15",
            "timestampEpoch": 1780783815,
            "temperature": 24.37,
        }

        with self.assertRaisesRegex(ValueError, "rssi"):
            WORKER.normalize_telemetry(payload)


if __name__ == "__main__":
    unittest.main()

import json
import os
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import psycopg


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_mqtt_config() -> tuple[str, int, str]:
    return (
        require_env("MQTT_HOST"),
        int(require_env("MQTT_PORT")),
        require_env("MQTT_TOPIC"),
    )


def get_db_config() -> dict:
    return {
        "dbname": require_env("POSTGRES_DB"),
        "user": require_env("POSTGRES_USER"),
        "password": require_env("POSTGRES_PASSWORD"),
        "host": require_env("POSTGRES_HOST"),
        "port": require_env("POSTGRES_PORT"),
    }


def db_connect():
    return psycopg.connect(**get_db_config())


def parse_payload(raw_payload: bytes) -> dict:
    data = json.loads(raw_payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("MQTT payload must be a JSON object")
    return data


def require_string(payload: dict, key: str) -> str:
    value = payload.get(key)
    if value is None or value == "":
        raise ValueError(f"Payload missing '{key}'")
    return str(value)


def require_non_negative_int(payload: dict, key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Payload field '{key}' must be a non-negative integer")
    return value


def require_int(payload: dict, key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Payload field '{key}' must be an integer")
    return value


def require_number(payload: dict, key: str) -> float:
    value = payload.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"Payload field '{key}' must be numeric")
    return float(value)


def normalize_optional_non_negative_int(payload: dict, key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Payload field '{key}' must be null or a non-negative integer")
    return value


def normalize_optional_temperature(payload: dict) -> float | None:
    value = payload.get("temperature")
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise ValueError("Payload field 'temperature' must be null or numeric")
    return float(value)


def normalize_optional_timestamp(payload: dict) -> str | None:
    value = payload.get("timestamp")
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("Payload field 'timestamp' must be null or a string")
    return value


def parse_recorded_at(payload: dict) -> datetime:
    timestamp = normalize_optional_timestamp(payload)
    if not timestamp:
        return datetime.now(timezone.utc)

    normalized_timestamp = timestamp.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized_timestamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_telemetry(payload: dict) -> dict:
    message_type = require_string(payload, "type")
    if message_type != "telemetry":
        raise ValueError(f"Unsupported payload type '{message_type}'")

    normalized = dict(payload)
    normalized["id"] = require_string(payload, "id")
    normalized["name"] = require_string(payload, "name")
    normalized["probeId"] = require_string(payload, "probeId")
    normalized["probeName"] = require_string(payload, "probeName")
    normalized["readingId"] = require_string(payload, "readingId")
    normalized["fw"] = require_string(payload, "fw")
    normalized["seq"] = require_non_negative_int(payload, "seq")
    normalized["receivedPackets"] = require_non_negative_int(payload, "receivedPackets")
    normalized["lostPackets"] = require_non_negative_int(payload, "lostPackets")
    normalized["timeSinceLastReceptionMs"] = normalize_optional_non_negative_int(
        payload, "timeSinceLastReceptionMs"
    )
    normalized["rssi"] = require_int(payload, "rssi")
    normalized["snr"] = require_number(payload, "snr")
    normalized["timestamp"] = normalize_optional_timestamp(payload)
    normalized["timestampEpoch"] = normalize_optional_non_negative_int(payload, "timestampEpoch")
    normalized["temperature"] = normalize_optional_temperature(payload)
    return normalized


def upsert_device(conn, payload: dict) -> int:
    hardware_id = payload["id"]
    name = payload["name"] or hardware_id
    firmware_version = payload["fw"]
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dashboard_device (name, hardware_id, firmware_version, is_active, last_seen_at, last_payload, created_at, updated_at)
            VALUES (%s, %s, %s, TRUE, %s, %s, %s, %s)
            ON CONFLICT (hardware_id) DO UPDATE
            SET name = EXCLUDED.name,
                firmware_version = EXCLUDED.firmware_version,
                last_seen_at = EXCLUDED.last_seen_at,
                last_payload = EXCLUDED.last_payload,
                updated_at = EXCLUDED.updated_at
            RETURNING id
            """,
            (name, hardware_id, firmware_version, now, json.dumps(payload), now, now),
        )
        return cur.fetchone()[0]


def insert_telemetry(conn, device_id: int, topic: str, payload: dict) -> None:
    recorded_at = parse_recorded_at(payload)
    temperature = payload["temperature"]
    reading_key = payload["readingId"]

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dashboard_telemetry (device_id, topic, reading_key, payload, temperature, recorded_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (reading_key) DO NOTHING
            """,
            (device_id, topic, reading_key, json.dumps(payload), temperature, recorded_at),
        )


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker with result code={reason_code}")
    mqtt_topic = (userdata or {}).get("mqtt_topic")
    if not mqtt_topic:
        raise RuntimeError("Missing MQTT topic in client user data")
    client.subscribe(mqtt_topic)


def on_message(client, userdata, msg):
    try:
        payload = normalize_telemetry(parse_payload(msg.payload))
        with db_connect() as conn:
            device_id = upsert_device(conn, payload)
            insert_telemetry(conn, device_id, msg.topic, payload)
            conn.commit()
        print(f"Stored telemetry from {payload.get('id')} on topic {msg.topic}")
    except Exception as exc:
        print(f"Failed to process message on {msg.topic}: {exc}")


def main():
    mqtt_host, mqtt_port, mqtt_topic = get_mqtt_config()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set({"mqtt_topic": mqtt_topic})
    client.connect(mqtt_host, mqtt_port, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()

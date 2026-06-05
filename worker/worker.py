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


MQTT_HOST = require_env("MQTT_HOST")
MQTT_PORT = int(require_env("MQTT_PORT"))
MQTT_TOPIC = require_env("MQTT_TOPIC")

DB_CONFIG = {
    "dbname": require_env("POSTGRES_DB"),
    "user": require_env("POSTGRES_USER"),
    "password": require_env("POSTGRES_PASSWORD"),
    "host": require_env("POSTGRES_HOST"),
    "port": require_env("POSTGRES_PORT"),
}


def db_connect():
    return psycopg.connect(**DB_CONFIG)


def parse_payload(raw_payload: bytes) -> dict:
    data = json.loads(raw_payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("MQTT payload must be a JSON object")
    return data


def build_reading_key(payload: dict) -> str | None:
    reading_id = payload.get("readingId")
    if reading_id:
        return str(reading_id)

    probe_id = payload.get("probeId")
    timestamp = payload.get("timestamp")
    if probe_id and timestamp:
        return f"{probe_id}|{timestamp}"

    return None


def upsert_device(conn, payload: dict) -> int:
    hardware_id = payload.get("id")
    if not hardware_id:
        raise ValueError("Payload missing 'id'")

    name = payload.get("name") or hardware_id
    firmware_version = payload.get("fw", "")
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
    recorded_at = datetime.now(timezone.utc)
    temperature = payload.get("temperature")
    reading_key = build_reading_key(payload)

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
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = parse_payload(msg.payload)
        with db_connect() as conn:
            device_id = upsert_device(conn, payload)
            insert_telemetry(conn, device_id, msg.topic, payload)
            conn.commit()
        print(f"Stored telemetry from {payload.get('id')} on topic {msg.topic}")
    except Exception as exc:
        print(f"Failed to process message on {msg.topic}: {exc}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()

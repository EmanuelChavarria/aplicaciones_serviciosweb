"""Configuración de la aplicación leída desde variables de entorno.

Ninguna credencial vive en el código: todo viene del archivo `.env` (que está
en `.gitignore`) o del entorno del sistema.
"""

import os
import re
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

# iot/sensors/{sensor_id}/data  ->  extrae {sensor_id}
_TOPIC_RE = re.compile(r"^iot/sensors/([^/]+)/data$")


def _sensor_desde_topico(topic: str) -> str | None:
    match = _TOPIC_RE.match(topic or "")
    return match.group(1) if match else None


@dataclass(frozen=True)
class Settings:
    # --- PostgreSQL ---
    database_url: str | None = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    db_host: str | None = field(default_factory=lambda: os.getenv("DB_HOST"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_name: str | None = field(default_factory=lambda: os.getenv("DB_NAME"))
    db_user: str | None = field(default_factory=lambda: os.getenv("DB_USER"))
    db_password: str | None = field(default_factory=lambda: os.getenv("DB_PASSWORD"))

    # --- MQTT ---
    mqtt_enabled: bool = field(
        default_factory=lambda: os.getenv("MQTT_ENABLED", "true").lower() in ("1", "true", "yes")
    )
    mqtt_broker: str | None = field(default_factory=lambda: os.getenv("MQTT_BROKER"))
    mqtt_port: int = field(default_factory=lambda: int(os.getenv("MQTT_PORT", "1883")))
    mqtt_topic: str = field(
        default_factory=lambda: os.getenv("MQTT_TOPIC", "iot/sensors/TEST-001/data")
    )
    mqtt_username: str | None = field(default_factory=lambda: os.getenv("MQTT_USERNAME"))
    mqtt_password: str | None = field(default_factory=lambda: os.getenv("MQTT_PASSWORD"))
    mqtt_keepalive: int = field(default_factory=lambda: int(os.getenv("MQTT_KEEPALIVE", "60")))

    # --- Sensor asignado ---
    # Si no se define SENSOR_CODIGO se deduce del tópico asignado.
    sensor_codigo: str | None = field(
        default_factory=lambda: os.getenv("SENSOR_CODIGO")
        or _sensor_desde_topico(os.getenv("MQTT_TOPIC", "iot/sensors/TEST-001/data"))
    )

    # --- Logs ---
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    log_file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "logs/app.log"))


def get_settings() -> Settings:
    """Se instancia en cada llamada para que los tests puedan cambiar el entorno."""
    return Settings()

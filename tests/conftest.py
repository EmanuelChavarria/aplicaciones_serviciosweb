"""Fixtures compartidas.

Las pruebas usan SQLite en memoria para no depender de PostgreSQL ni del
broker. Las tablas se crean AQUÍ (solo en pruebas); la aplicación real nunca
ejecuta `create_all` porque el esquema ya existe en PostgreSQL.
"""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Antes de importar la app: sin MQTT real y sin archivo de log.
os.environ["MQTT_ENABLED"] = "false"
os.environ["LOG_FILE"] = ""

from app.database import connection  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Medicion, Sensor, SensorMagnitud  # noqa: E402

SENSOR = "TEST-001"


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    connection.Base.metadata.create_all(engine)
    connection.configure_engine(engine)

    session = connection.get_session_factory()()
    s1 = Sensor(id=1, codigo=SENSOR, nombre="Sensor de prueba", categoria="AMBIENTE",
                ubicacion="Laboratorio", activo=True)
    s2 = Sensor(id=2, codigo="INACT-001", nombre="Sensor apagado", categoria="AIRE",
                ubicacion="Bodega", activo=False)
    s3 = Sensor(id=3, codigo="OTRO-001", nombre="Sensor de otro grupo", categoria="GAS",
                ubicacion="Patio", activo=True)
    session.add_all([s1, s2, s3])
    session.add_all([
        SensorMagnitud(id=1, sensor_id=1, magnitud="temperature", unidad="C",
                       valor_minimo=Decimal("-40"), valor_maximo=Decimal("85")),
        SensorMagnitud(id=2, sensor_id=1, magnitud="humidity", unidad="%",
                       valor_minimo=Decimal("0"), valor_maximo=Decimal("100")),
        SensorMagnitud(id=3, sensor_id=2, magnitud="temperature", unidad="C",
                       valor_minimo=Decimal("-40"), valor_maximo=Decimal("85")),
        SensorMagnitud(id=4, sensor_id=3, magnitud="co2", unidad="ppm",
                       valor_minimo=Decimal("0"), valor_maximo=Decimal("5000")),
    ])
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def client(db: Session):
    with TestClient(app) as c:
        yield c


def payload(**cambios) -> str:
    """Payload válido de referencia; `cambios` lo modifica para armar casos inválidos."""
    base = {
        "sensor_id": SENSOR,
        "timestamp": "2026-10-07T16:25:30Z",
        "measurements": {
            "temperature": {"value": 24.6, "unit": "C"},
            "humidity": {"value": 55, "unit": "%"},
        },
    }
    base.update(cambios)
    return json.dumps(base)


def insertar_medicion(db: Session, sm_id: int, valor: str, ts: datetime) -> Medicion:
    m = Medicion(sensor_magnitud_id=sm_id, valor=Decimal(valor), timestamp_utc=ts)
    db.add(m)
    db.commit()
    return m


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)

"""Pruebas de la ingesta MQTT (evidencias 1 a 7 y 17).

Cada prueba indica en su nombre el número de evidencia de la guía.
"""

import json
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import select

from app.config import Settings
from app.models import Medicion
from app.mqtt.client import crear_cliente
from app.services.ingesta import procesar_mensaje
from tests.conftest import SENSOR, payload


def contar(db) -> int:
    return len(db.scalars(select(Medicion)).all())


# --- Evidencia 1: recepción MQTT ---------------------------------------------
def test_01_callback_mqtt_recibe_y_guarda(db):
    settings = Settings(mqtt_broker="localhost", sensor_codigo=SENSOR)
    cliente = crear_cliente(settings)
    mensaje = SimpleNamespace(topic=f"iot/sensors/{SENSOR}/data", payload=payload().encode())

    cliente.on_message(cliente, None, mensaje)  # simula la llegada desde el broker

    assert contar(db) == 2


# --- Evidencia 2: medición válida -------------------------------------------
def test_02_medicion_valida_se_almacena_una_fila_por_magnitud(db):
    r = procesar_mensaje(db, payload(), SENSOR)

    assert r.aceptado and r.codigo == "OK" and r.mediciones_guardadas == 2
    filas = db.scalars(select(Medicion).order_by(Medicion.sensor_magnitud_id)).all()
    assert [f.sensor_magnitud_id for f in filas] == [1, 2]
    assert [f.valor for f in filas] == [Decimal("24.6"), Decimal("55")]
    # mismo timestamp para todas las magnitudes del payload, guardado en UTC
    assert {f.timestamp_utc.replace(tzinfo=timezone.utc) for f in filas} == {
        datetime(2026, 10, 7, 16, 25, 30, tzinfo=timezone.utc)
    }


# --- Evidencia 3: sensor inexistente -----------------------------------------
def test_03_sensor_inexistente(db):
    r = procesar_mensaje(db, payload(sensor_id="NO-EXISTE"), SENSOR)
    assert (r.aceptado, r.codigo) == (False, "SENSOR_INEXISTENTE")
    assert contar(db) == 0


# --- Evidencia 4: unidad incorrecta ------------------------------------------
def test_04_unidad_incorrecta(db):
    medidas = {"temperature": {"value": 24.6, "unit": "F"}}
    r = procesar_mensaje(db, payload(measurements=medidas), SENSOR)
    assert (r.aceptado, r.codigo) == (False, "UNIDAD_INVALIDA")
    assert contar(db) == 0


# --- Evidencia 5: tipo de dato incorrecto ------------------------------------
def test_05_tipo_de_dato_incorrecto_texto(db):
    medidas = {"temperature": {"value": "24.6", "unit": "C"}}
    r = procesar_mensaje(db, payload(measurements=medidas), SENSOR)
    assert (r.aceptado, r.codigo) == (False, "TIPO_DATO_INVALIDO")
    assert contar(db) == 0


def test_05_tipo_de_dato_incorrecto_booleano(db):
    medidas = {"temperature": {"value": True, "unit": "C"}}
    r = procesar_mensaje(db, payload(measurements=medidas), SENSOR)
    assert (r.aceptado, r.codigo) == (False, "TIPO_DATO_INVALIDO")


def test_05_json_roto_y_campos_faltantes(db):
    assert procesar_mensaje(db, "{no es json", SENSOR).codigo == "JSON_INVALIDO"
    assert procesar_mensaje(db, b"\xff\xfe", SENSOR).codigo == "JSON_INVALIDO"
    sin_medidas = json.dumps({"sensor_id": SENSOR, "timestamp": "2026-10-07T16:25:30Z"})
    assert procesar_mensaje(db, sin_medidas, SENSOR).codigo == "ESTRUCTURA_INVALIDA"
    assert procesar_mensaje(db, "[1, 2, 3]", SENSOR).codigo == "ESTRUCTURA_INVALIDA"
    assert contar(db) == 0


# --- Evidencia 6: magnitud incorrecta ----------------------------------------
def test_06_magnitud_incorrecta(db):
    medidas = {"pressure": {"value": 1013, "unit": "hPa"}}
    r = procesar_mensaje(db, payload(measurements=medidas), SENSOR)
    assert (r.aceptado, r.codigo) == (False, "MAGNITUD_INVALIDA")
    assert contar(db) == 0


# --- Evidencia 7: timestamp inválido -----------------------------------------
def test_07_timestamp_invalido(db):
    for malo in ["ayer", "2026-10-07", "2026-10-07T16:25:30", "2026-13-45T10:00:00Z", 1759854330, None]:
        r = procesar_mensaje(db, payload(timestamp=malo), SENSOR)
        assert (r.aceptado, r.codigo) == (False, "TIMESTAMP_INVALIDO"), malo
    assert contar(db) == 0


def test_07_timestamp_con_offset_se_normaliza_a_utc(db):
    r = procesar_mensaje(db, payload(timestamp="2026-10-07T11:25:30-05:00"), SENSOR)
    assert r.aceptado
    fila = db.scalars(select(Medicion)).first()
    assert fila.timestamp_utc.replace(tzinfo=timezone.utc) == datetime(
        2026, 10, 7, 16, 25, 30, tzinfo=timezone.utc
    )


# --- Reglas de negocio adicionales -------------------------------------------
def test_sensor_inactivo_y_sensor_no_asignado(db):
    inactivo = payload(
        sensor_id="INACT-001", measurements={"temperature": {"value": 20, "unit": "C"}}
    )
    assert procesar_mensaje(db, inactivo, None).codigo == "SENSOR_INACTIVO"

    otro = payload(sensor_id="OTRO-001", measurements={"co2": {"value": 400, "unit": "ppm"}})
    assert procesar_mensaje(db, otro, SENSOR).codigo == "SENSOR_NO_ASIGNADO"
    assert contar(db) == 0


def test_valor_fuera_de_rango(db):
    medidas = {"temperature": {"value": 500, "unit": "C"}}
    r = procesar_mensaje(db, payload(measurements=medidas), SENSOR)
    assert (r.aceptado, r.codigo) == (False, "VALOR_FUERA_DE_RANGO")


def test_todo_o_nada_si_una_magnitud_es_invalida_no_se_guarda_ninguna(db):
    medidas = {
        "temperature": {"value": 24.6, "unit": "C"},  # válida
        "humidity": {"value": 55, "unit": "ppm"},  # unidad incorrecta
    }
    r = procesar_mensaje(db, payload(measurements=medidas), SENSOR)
    assert (r.aceptado, r.codigo) == (False, "UNIDAD_INVALIDA")
    assert contar(db) == 0  # ni siquiera la temperatura válida


# --- Evidencia 17: claves foráneas ------------------------------------------
def test_17_claves_foraneas_se_navegan_medicion_a_magnitud_a_sensor(db):
    procesar_mensaje(db, payload(), SENSOR)
    m = db.scalars(select(Medicion).order_by(Medicion.id)).first()
    assert m.sensor_magnitud.magnitud == "temperature"
    assert m.sensor_magnitud.sensor.codigo == SENSOR
    assert len(m.sensor_magnitud.sensor.magnitudes) == 2

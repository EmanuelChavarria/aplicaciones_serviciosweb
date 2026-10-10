"""Lógica de negocio de la ingesta MQTT.

Este módulo es el puente entre las capas y NO conoce MQTT ni HTTP: recibe los
bytes de un mensaje y devuelve un `ResultadoIngesta`. Gracias a eso se puede
probar sin broker y sin servidor web.

Pipeline (cada paso rechaza el mensaje completo si falla):
    1. JSON válido                         -> JSON_INVALIDO
    2. Estructura/tipos/timestamp (Pydantic) -> ESTRUCTURA_INVALIDA | TIPO_DATO_INVALIDO | TIMESTAMP_INVALIDO
    3. El sensor existe en BD (ORM)        -> SENSOR_INEXISTENTE
    4. Es el sensor asignado al grupo      -> SENSOR_NO_ASIGNADO
    5. El sensor está activo               -> SENSOR_INACTIVO
    6. Cada magnitud pertenece al sensor   -> MAGNITUD_INVALIDA
    7. La unidad coincide                  -> UNIDAD_INVALIDA
    8. El valor está en [mínimo, máximo]   -> VALOR_FUERA_DE_RANGO
    9. Se guardan TODAS las magnitudes en una transacción -> ERROR_BD si falla
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.crud import medicion as crud_medicion
from app.crud import sensor as crud_sensor
from app.crud import sensor_magnitud as crud_sensor_magnitud
from app.schemas.medicion import PayloadMQTT

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoIngesta:
    aceptado: bool
    codigo: str  # "OK" o el código de rechazo (ver docstring del módulo)
    detalle: str
    mediciones_guardadas: int = 0


def _rechazo(codigo: str, detalle: str) -> ResultadoIngesta:
    return ResultadoIngesta(aceptado=False, codigo=codigo, detalle=detalle)


def _clasificar_error_pydantic(error: ValidationError) -> tuple[str, str]:
    """Convierte el primer error de Pydantic en un código de rechazo legible."""
    primero = error.errors()[0]
    ruta = ".".join(str(p) for p in primero["loc"])
    detalle = f"{ruta or 'payload'}: {primero['msg']}"

    if "timestamp" in primero["loc"]:
        return "TIMESTAMP_INVALIDO", detalle
    if "value" in primero["loc"]:
        return "TIPO_DATO_INVALIDO", detalle
    return "ESTRUCTURA_INVALIDA", detalle


def procesar_mensaje(
    db: Session,
    raw: bytes | str,
    sensor_asignado: str | None = None,
) -> ResultadoIngesta:
    """Valida un mensaje MQTT y, si es totalmente válido, lo almacena."""

    # 1) JSON -----------------------------------------------------------
    try:
        texto = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        datos = json.loads(texto)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _rechazo("JSON_INVALIDO", f"el mensaje no es JSON válido: {exc}")

    # 2) Estructura, tipos y timestamp (Pydantic) ------------------------
    try:
        payload = PayloadMQTT.model_validate(datos)
    except ValidationError as exc:
        codigo, detalle = _clasificar_error_pydantic(exc)
        return _rechazo(codigo, detalle)

    # 3-5) Sensor (ORM) --------------------------------------------------
    sensor = crud_sensor.get_by_codigo(db, payload.sensor_id)
    if sensor is None:
        return _rechazo("SENSOR_INEXISTENTE", f"no existe un sensor con codigo '{payload.sensor_id}'")

    if sensor_asignado and sensor.codigo != sensor_asignado:
        return _rechazo(
            "SENSOR_NO_ASIGNADO",
            f"el sensor '{sensor.codigo}' no es el asignado a este grupo ('{sensor_asignado}')",
        )

    if not sensor.activo:
        return _rechazo("SENSOR_INACTIVO", f"el sensor '{sensor.codigo}' está inactivo")

    # 6-8) Magnitud, unidad y rango: TODAS deben ser válidas ----------------
    por_guardar: list[tuple[int, Decimal, datetime]] = []
    for nombre_magnitud, medida in payload.measurements.items():
        sm = crud_sensor_magnitud.get_by_sensor_and_magnitud(db, sensor.id, nombre_magnitud)
        if sm is None:
            return _rechazo(
                "MAGNITUD_INVALIDA",
                f"el sensor '{sensor.codigo}' no mide la magnitud '{nombre_magnitud}'",
            )

        if medida.unit != sm.unidad:
            return _rechazo(
                "UNIDAD_INVALIDA",
                f"'{nombre_magnitud}' debe venir en '{sm.unidad}', llegó '{medida.unit}'",
            )

        # str() evita artefactos de float al pasar a Decimal (24.6 -> 24.6, no 24.60000000000000142...)
        valor = Decimal(str(medida.value))
        if not (sm.valor_minimo <= valor <= sm.valor_maximo):
            return _rechazo(
                "VALOR_FUERA_DE_RANGO",
                f"'{nombre_magnitud}'={valor} fuera del rango "
                f"[{sm.valor_minimo}, {sm.valor_maximo}] {sm.unidad}",
            )

        por_guardar.append((sm.id, valor, payload.timestamp))

    # 9) Persistencia atómica (todo el payload o nada) ----------------------
    try:
        guardadas = crud_medicion.create_many(db, por_guardar)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Error de base de datos al guardar el payload")
        return _rechazo("ERROR_BD", f"no se pudo guardar: {exc.__class__.__name__}")

    return ResultadoIngesta(
        aceptado=True,
        codigo="OK",
        detalle=f"{guardadas} medición(es) del sensor '{sensor.codigo}' guardadas",
        mediciones_guardadas=guardadas,
    )

"""Schemas de mediciones.

Hay dos grupos con responsabilidades distintas:

1. `MedidaPayload` / `PayloadMQTT`: validan la ESTRUCTURA del mensaje que llega
   por MQTT (campos obligatorios, tipos, formato del timestamp). No saben nada
   de la base de datos.
2. `MedicionOut` / `UltimaMedicionOut`: forma de las respuestas HTTP.
"""

import math
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    StrictFloat,
    StrictInt,
    StrictStr,
    TypeAdapter,
    field_validator,
)

from app.utils.tiempo import formatear_hora_colombia

if TYPE_CHECKING:
    from app.models.medicion import Medicion

# ---------------------------------------------------------------------------
# Entrada: payload MQTT
# ---------------------------------------------------------------------------

# Exige fecha + hora + zona explícita (Z o ±HH:MM). Rechaza "2026-10-07",
# "1759854330" o "2026-10-07T16:25:30" (sin zona), que Pydantic aceptaría en
# modo laxo pero que no son un timestamp UTC válido para este taller.
_ISO_8601_CON_ZONA = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?(Z|[+-]\d{2}:\d{2})$"
)
_aware_datetime = TypeAdapter(AwareDatetime)


class MedidaPayload(BaseModel):
    """Una magnitud dentro de `measurements`: `{"value": 24.6, "unit": "C"}`."""

    # StrictInt/StrictFloat: "24.6" (texto) o true (booleano) se rechazan.
    value: StrictInt | StrictFloat
    unit: StrictStr = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def _valor_finito(cls, v: int | float) -> float:
        if not math.isfinite(v):
            raise ValueError("el valor debe ser un número finito (no NaN ni infinito)")
        return float(v)

    @field_validator("unit")
    @classmethod
    def _unidad_sin_espacios(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("la unidad no puede estar vacía")
        return v


class PayloadMQTT(BaseModel):
    """Mensaje completo publicado por el sensor."""

    sensor_id: StrictStr = Field(min_length=1, max_length=20)
    timestamp: datetime
    measurements: dict[str, MedidaPayload] = Field(min_length=1)

    @field_validator("sensor_id")
    @classmethod
    def _sensor_sin_espacios(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("sensor_id no puede estar vacío")
        return v

    @field_validator("timestamp", mode="before")
    @classmethod
    def _timestamp_utc(cls, v: object) -> datetime:
        if not isinstance(v, str) or not _ISO_8601_CON_ZONA.match(v):
            raise ValueError(
                "timestamp debe ser texto ISO 8601 con zona, p. ej. 2026-10-07T16:25:30Z"
            )
        # Normaliza a UTC: es lo que se almacena.
        return _aware_datetime.validate_python(v).astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Salida: respuestas HTTP
# ---------------------------------------------------------------------------


class MedicionOut(BaseModel):
    id: int
    sensor_magnitud_id: int
    sensor_id: int
    sensor_codigo: str
    magnitud: str
    unidad: str
    valor: float
    timestamp_colombia: str
    fecha_recepcion_colombia: str

    @classmethod
    def desde_orm(cls, m: "Medicion") -> "MedicionOut":
        sm = m.sensor_magnitud
        return cls(
            id=m.id,
            sensor_magnitud_id=m.sensor_magnitud_id,
            sensor_id=sm.sensor_id,
            sensor_codigo=sm.sensor.codigo,
            magnitud=sm.magnitud,
            unidad=sm.unidad,
            valor=float(m.valor),
            timestamp_colombia=formatear_hora_colombia(m.timestamp_utc),
            fecha_recepcion_colombia=formatear_hora_colombia(m.fecha_recepcion),
        )


class UltimaMedicionOut(BaseModel):
    """Última lectura de un sensor: todas las magnitudes de su payload más reciente."""

    sensor_id: int
    sensor_codigo: str
    timestamp_colombia: str
    mediciones: list[MedicionOut]

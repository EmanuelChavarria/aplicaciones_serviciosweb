"""CRUD de `mediciones`: Create (lo hace el consumidor MQTT) y Read (lo hace la API).

No hay Update ni Delete: el histórico de mediciones es inmutable (y la FK
`ON DELETE RESTRICT` protege las magnitudes que ya tienen datos).
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.medicion import Medicion
from app.models.sensor_magnitud import SensorMagnitud

# Carga la magnitud y el sensor en la misma consulta (evita el problema N+1).
_CON_RELACIONES = joinedload(Medicion.sensor_magnitud).joinedload(SensorMagnitud.sensor)


# ----------------------------- Create -----------------------------


def create_many(
    db: Session,
    items: list[tuple[int, Decimal, datetime]],
) -> int:
    """Inserta varias mediciones en UNA sola transacción (todo o nada).

    `items` es una lista de `(sensor_magnitud_id, valor, timestamp_utc)`.
    Si algo falla, el llamador debe hacer `rollback()`; aquí no se captura la
    excepción para no ocultar errores.
    """
    db.add_all(
        Medicion(sensor_magnitud_id=sm_id, valor=valor, timestamp_utc=ts)
        for sm_id, valor, ts in items
    )
    db.commit()
    return len(items)


# ------------------------------ Read ------------------------------


def get(db: Session, medicion_id: int) -> Medicion | None:
    return db.scalar(select(Medicion).options(_CON_RELACIONES).where(Medicion.id == medicion_id))


def list_by_sensor(
    db: Session,
    sensor_id: int,
    *,
    magnitud: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limit: int | None = None,
) -> list[Medicion]:
    """Histórico de un sensor, más recientes primero. Todos los filtros se combinan.

    `limit` devuelve las ÚLTIMAS N mediciones (por eso el orden es descendente
    y el LIMIT se aplica después del filtrado).
    """
    stmt = (
        select(Medicion)
        .join(Medicion.sensor_magnitud)
        .options(_CON_RELACIONES)
        .where(SensorMagnitud.sensor_id == sensor_id)
    )
    if magnitud is not None:
        stmt = stmt.where(SensorMagnitud.magnitud == magnitud)
    if desde is not None:
        stmt = stmt.where(Medicion.timestamp_utc >= desde)
    if hasta is not None:
        stmt = stmt.where(Medicion.timestamp_utc <= hasta)

    stmt = stmt.order_by(Medicion.timestamp_utc.desc(), Medicion.id.desc())
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).unique())


def ultima_by_sensor(db: Session, sensor_id: int) -> list[Medicion]:
    """Todas las mediciones del timestamp más reciente del sensor.

    Un payload con varias magnitudes genera varias filas con el mismo
    `timestamp_utc`; la "última medición" es ese conjunto completo.
    """
    ultimo_ts = db.scalar(
        select(Medicion.timestamp_utc)
        .join(Medicion.sensor_magnitud)
        .where(SensorMagnitud.sensor_id == sensor_id)
        .order_by(Medicion.timestamp_utc.desc())
        .limit(1)
    )
    if ultimo_ts is None:
        return []

    stmt = (
        select(Medicion)
        .join(Medicion.sensor_magnitud)
        .options(_CON_RELACIONES)
        .where(SensorMagnitud.sensor_id == sensor_id, Medicion.timestamp_utc == ultimo_ts)
        .order_by(Medicion.sensor_magnitud_id)
    )
    return list(db.scalars(stmt).unique())

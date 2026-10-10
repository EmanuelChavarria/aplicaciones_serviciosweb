"""CRUD de `sensor_magnitudes`: solo lectura (catálogo del docente)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor_magnitud import SensorMagnitud


def get(db: Session, sensor_magnitud_id: int) -> SensorMagnitud | None:
    return db.get(SensorMagnitud, sensor_magnitud_id)


def list_by_sensor(db: Session, sensor_id: int) -> list[SensorMagnitud]:
    return list(
        db.scalars(
            select(SensorMagnitud)
            .where(SensorMagnitud.sensor_id == sensor_id)
            .order_by(SensorMagnitud.id)
        )
    )


def get_by_sensor_and_magnitud(
    db: Session, sensor_id: int, magnitud: str
) -> SensorMagnitud | None:
    """Garantizada por `UNIQUE(sensor_id, magnitud)` en BD: devuelve 0 o 1 fila."""
    return db.scalar(
        select(SensorMagnitud).where(
            SensorMagnitud.sensor_id == sensor_id, SensorMagnitud.magnitud == magnitud
        )
    )

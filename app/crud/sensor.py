"""CRUD de `sensores`: solo lectura.

El catálogo lo suministra el docente; la aplicación no crea, modifica ni
elimina sensores, por eso este módulo únicamente expone operaciones Read.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor import Sensor


def get(db: Session, sensor_id: int) -> Sensor | None:
    return db.get(Sensor, sensor_id)


def get_by_codigo(db: Session, codigo: str) -> Sensor | None:
    return db.scalar(select(Sensor).where(Sensor.codigo == codigo))


def list_all(db: Session) -> list[Sensor]:
    return list(db.scalars(select(Sensor).order_by(Sensor.id)))

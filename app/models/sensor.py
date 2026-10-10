from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.sensor_magnitud import SensorMagnitud


class Sensor(Base):
    """Tabla `sensores` (catálogo de solo lectura para la aplicación)."""

    __tablename__ = "sensores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    categoria: Mapped[str] = mapped_column(String(30), nullable=False)  # AIRE|GAS|AGUA|AMBIENTE
    ubicacion: Mapped[str] = mapped_column(String(100), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    magnitudes: Mapped[list["SensorMagnitud"]] = relationship(
        back_populates="sensor", order_by="SensorMagnitud.id"
    )

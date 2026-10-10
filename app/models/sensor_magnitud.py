from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.medicion import Medicion
    from app.models.sensor import Sensor


class SensorMagnitud(Base):
    """Tabla `sensor_magnitudes`: qué magnitudes mide cada sensor, su unidad y rango.

    En BD existen además `UNIQUE(sensor_id, magnitud)` y
    `CHECK (valor_minimo < valor_maximo)`; aquí no hace falta repetirlos porque
    el ORM no crea el esquema.
    """

    __tablename__ = "sensor_magnitudes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sensor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sensores.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    magnitud: Mapped[str] = mapped_column(String(50), nullable=False)
    unidad: Mapped[str] = mapped_column(String(20), nullable=False)
    valor_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    valor_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    sensor: Mapped["Sensor"] = relationship(back_populates="magnitudes")
    mediciones: Mapped[list["Medicion"]] = relationship(back_populates="sensor_magnitud")

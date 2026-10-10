"""Importar todos los modelos aquí garantiza que SQLAlchemy resuelva las relaciones."""

from app.models.medicion import Medicion
from app.models.sensor import Sensor
from app.models.sensor_magnitud import SensorMagnitud

__all__ = ["Sensor", "SensorMagnitud", "Medicion"]

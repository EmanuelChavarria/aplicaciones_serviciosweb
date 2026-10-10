"""Actividad 1, paso 7: verifica la conexión con PostgreSQL y muestra el catálogo.

Uso (desde la raíz del repo, con el entorno virtual activo):
    python -m scripts.verificar_conexion
"""

from sqlalchemy import func, select

from app.database.connection import get_session_factory, verificar_conexion
from app.models import Medicion, Sensor, SensorMagnitud


def main() -> None:
    verificar_conexion()
    print("Conexión con PostgreSQL: OK")

    with get_session_factory()() as db:
        print("Sensores:        ", db.scalar(select(func.count()).select_from(Sensor)))
        print("Sensor-magnitudes:", db.scalar(select(func.count()).select_from(SensorMagnitud)))
        print("Mediciones:      ", db.scalar(select(func.count()).select_from(Medicion)))


if __name__ == "__main__":
    main()

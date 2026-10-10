"""Utilidades de zona horaria.

Regla del taller: en base de datos todo se guarda en UTC; solo las respuestas
GET se convierten a hora local de Colombia (America/Bogota, UTC-05:00, sin
horario de verano).
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

COLOMBIA = ZoneInfo("America/Bogota")


def asegurar_utc(valor: datetime) -> datetime:
    """Devuelve `valor` como datetime con zona UTC.

    Si llega sin zona (ocurre con SQLite en pruebas) se asume que ya es UTC.
    """
    if valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(timezone.utc)


def desde_hora_local(valor: datetime) -> datetime:
    """Interpreta una fecha de consulta (`desde`/`hasta`) y la lleva a UTC.

    - Con zona (`Z` o `-05:00`): se respeta.
    - Sin zona: se interpreta como hora de Colombia, porque es la hora en la
      que la API responde.
    """
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=COLOMBIA)
    return valor.astimezone(timezone.utc)


def formatear_hora_colombia(valor: datetime) -> str:
    """`2026-10-07 11:25:30 (UTC-05:00)` — legible y siempre con el mismo formato."""
    local = asegurar_utc(valor).astimezone(COLOMBIA)
    return local.strftime("%Y-%m-%d %H:%M:%S") + " (UTC-05:00)"

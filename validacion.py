"""
validacion.py

Aplica las reglas de negocio del contrato institucional sobre una
Medicion YA normalizada (tipos correctos). No reemplaza la validacion
del servidor: es un filtro previo para no desperdiciar llamadas HTTP
en datos que seguro seran rechazados.
"""

from typing import Optional, Tuple

from contrato import Medicion, ORIGENES_VALIDOS


def validar_medicion(medicion: Medicion) -> Tuple[bool, Optional[str]]:
    """Devuelve (es_valida, motivo_rechazo)."""

    if not medicion.ciudad or not medicion.ciudad.strip():
        return False, "ciudad vacia"

    if not medicion.pais or not medicion.pais.strip():
        return False, "pais vacio"

    if medicion.latitud is None or not (-90 <= medicion.latitud <= 90):
        return False, f"latitud fuera de rango (-90 a 90): {medicion.latitud}"

    if medicion.longitud is None or not (-180 <= medicion.longitud <= 180):
        return False, f"longitud fuera de rango (-180 a 180): {medicion.longitud}"

    if medicion.temperatura_c is None:
        return False, "temperatura_c no numerica"

    if medicion.humedad is None or not (0 <= medicion.humedad <= 100):
        return False, f"humedad fuera de rango (0 a 100): {medicion.humedad}"

    if medicion.viento_kmh is None or medicion.viento_kmh < 0:
        return False, f"viento_kmh negativo: {medicion.viento_kmh}"

    if not medicion.fecha_hora:
        return False, "fecha_hora invalida"

    if medicion.origen not in ORIGENES_VALIDOS:
        return False, f"origen no permitido: {medicion.origen}"

    return True, None

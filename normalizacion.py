"""
normalizacion.py

Transforma registros crudos de cada proveedor a un objeto Medicion
compatible con el contrato institucional.

Criterio adoptado (documentado tambien en ANALISIS.md):
- Si un valor no puede convertirse al TIPO exigido por el contrato
  (falta el campo, no es numerico, la fecha no es interpretable, etc.)
  se considera un ERROR DE NORMALIZACION: la funcion devuelve
  (None, "motivo").
- Si el valor SI puede representarse en el tipo correcto pero incumple
  una regla de negocio (ej. texto vacio, fuera de rango) la
  normalizacion se da por exitosa; esa regla la evalua la etapa de
  validacion local (validacion.py).
"""

from datetime import datetime
from typing import Optional, Tuple

from contrato import Medicion

FACTOR_MS_A_KMH = 3.6
ZONA_HORARIA_ASUMIDA = "-05:00"  # Colombia (COT). Ver supuesto en ANALISIS.md


def _f_a_c(temperatura_f: float) -> float:
    return (temperatura_f - 32) * 5 / 9


def _ms_a_kmh(velocidad_ms: float) -> float:
    return velocidad_ms * FACTOR_MS_A_KMH


def _a_float(valor) -> Optional[float]:
    """Intenta convertir un valor a float. Devuelve None si no es posible."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        texto = valor.strip()
        if texto == "":
            return None
        try:
            return float(texto)
        except ValueError:
            return None
    return None


def _texto_no_vacio_o_none(valor) -> Optional[str]:
    """
    Devuelve el texto tal cual si es una cadena (incluso vacia: la
    validez de negocio se evalua despues). Devuelve None solo si el
    campo no existe o no es representable como texto.
    """
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor
    return None


def normalizar_registro_a(crudo: dict) -> Tuple[Optional[Medicion], Optional[str]]:
    """Normaliza un registro del proveedor A (JSON, unidades imperiales/metricas mixtas)."""
    station = crudo.get("station") or {}
    location = crudo.get("location") or {}
    measurements = crudo.get("measurements") or {}

    ciudad = _texto_no_vacio_o_none(station.get("city_name"))
    pais = _texto_no_vacio_o_none(station.get("country_code"))

    latitud = _a_float(location.get("lat"))
    longitud = _a_float(location.get("lon"))

    temperatura_f = _a_float(measurements.get("temperature_f"))
    humedad = _a_float(measurements.get("relative_humidity"))
    viento_ms = _a_float(measurements.get("wind_speed_ms"))

    fecha_iso = _parsear_fecha_iso(crudo.get("observed_at"))

    faltantes = []
    if ciudad is None:
        faltantes.append("ciudad (station.city_name)")
    if pais is None:
        faltantes.append("pais (station.country_code)")
    if latitud is None:
        faltantes.append("latitud (location.lat)")
    if longitud is None:
        faltantes.append("longitud (location.lon)")
    if temperatura_f is None:
        faltantes.append("temperatura_c (measurements.temperature_f)")
    if humedad is None:
        faltantes.append("humedad (measurements.relative_humidity)")
    if viento_ms is None:
        faltantes.append("viento_kmh (measurements.wind_speed_ms)")
    if fecha_iso is None:
        faltantes.append("fecha_hora (observed_at)")

    if faltantes:
        return None, "No se pudo convertir: " + ", ".join(faltantes)

    medicion = Medicion(
        ciudad=ciudad,
        pais=pais,
        latitud=latitud,
        longitud=longitud,
        temperatura_c=round(_f_a_c(temperatura_f), 2),
        humedad=humedad,
        viento_kmh=round(_ms_a_kmh(viento_ms), 2),
        fecha_hora=fecha_iso,
        origen="proveedor_a",
    )
    return medicion, None


def normalizar_registro_b(crudo: dict) -> Tuple[Optional[Medicion], Optional[str]]:
    """Normaliza un registro del proveedor B (CSV, unidades ya metricas salvo fecha)."""
    if "__error_fila__" in crudo:
        return None, f"Fila CSV defectuosa: {crudo['__error_fila__']}"

    ciudad = _texto_no_vacio_o_none(crudo.get("municipality"))
    pais = _texto_no_vacio_o_none(crudo.get("country"))

    latitud = _a_float(crudo.get("latitude_deg"))
    longitud = _a_float(crudo.get("longitude_deg"))
    temperatura_c = _a_float(crudo.get("temp_celsius"))
    humedad = _a_float(crudo.get("humidity_pct"))
    viento_kmh = _a_float(crudo.get("wind_kmh"))

    fecha_iso = _parsear_fecha_proveedor_b(crudo.get("measurement_time"))

    faltantes = []
    if ciudad is None:
        faltantes.append("ciudad (municipality)")
    if pais is None:
        faltantes.append("pais (country)")
    if latitud is None:
        faltantes.append("latitud (latitude_deg)")
    if longitud is None:
        faltantes.append("longitud (longitude_deg)")
    if temperatura_c is None:
        faltantes.append("temperatura_c (temp_celsius)")
    if humedad is None:
        faltantes.append("humedad (humidity_pct)")
    if viento_kmh is None:
        faltantes.append("viento_kmh (wind_kmh)")
    if fecha_iso is None:
        faltantes.append("fecha_hora (measurement_time)")

    if faltantes:
        return None, "No se pudo convertir: " + ", ".join(faltantes)

    medicion = Medicion(
        ciudad=ciudad,
        pais=pais,
        latitud=latitud,
        longitud=longitud,
        temperatura_c=round(temperatura_c, 2),
        humedad=humedad,
        viento_kmh=round(viento_kmh, 2),
        fecha_hora=fecha_iso,
        origen="proveedor_b",
    )
    return medicion, None


def _parsear_fecha_iso(valor) -> Optional[str]:
    """El proveedor A ya entrega fecha en ISO 8601; solo se valida y normaliza."""
    if not isinstance(valor, str) or not valor.strip():
        return None
    try:
        dt = datetime.fromisoformat(valor)
    except ValueError:
        return None
    return dt.isoformat()


def _parsear_fecha_proveedor_b(valor) -> Optional[str]:
    """El proveedor B entrega 'DD/MM/YYYY HH:MM' en hora local; se convierte a ISO 8601."""
    if not isinstance(valor, str) or not valor.strip():
        return None
    try:
        dt = datetime.strptime(valor.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        return None
    return dt.isoformat() + ZONA_HORARIA_ASUMIDA

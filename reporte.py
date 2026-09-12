"""
reporte.py

Construye las evidencias del proceso de integracion:
- salida/normalizadas.json
- salida/reporte.json
"""

import json
import os
from typing import List

from contrato import RegistroProcesado


def escribir_normalizadas(registros: List[RegistroProcesado], ruta: str) -> None:
    """
    Incluye todo registro que SI pudo normalizarse, sin importar si
    luego fue rechazado por la validacion local (o incluso por la API).
    Excluye unicamente los que tuvieron error de normalizacion.
    """
    salida = [
        r.medicion.to_dict()
        for r in registros
        if r.estado != "error_normalizacion" and r.medicion is not None
    ]
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)


def construir_reporte(registros: List[RegistroProcesado], equipo: str, consulta_final: dict) -> dict:
    conteos = {
        "procesados": len(registros),
        "normalizados": sum(1 for r in registros if r.estado != "error_normalizacion"),
        "errores_normalizacion": sum(1 for r in registros if r.estado == "error_normalizacion"),
        "validos_localmente": sum(
            1 for r in registros if r.estado in ("enviado", "aceptado_api", "rechazado_api", "error_comunicacion")
        ),
        "rechazados_localmente": sum(1 for r in registros if r.estado == "rechazado_local"),
        "enviados": sum(
            1 for r in registros if r.estado in ("aceptado_api", "rechazado_api", "error_comunicacion")
        ),
        "aceptados_por_api": sum(1 for r in registros if r.estado == "aceptado_api"),
        "rechazados_por_api": sum(1 for r in registros if r.estado == "rechazado_api"),
        "errores_comunicacion": sum(1 for r in registros if r.estado == "error_comunicacion"),
    }

    return {
        "equipo": equipo,
        "resumen": conteos,
        "consulta_final_api": consulta_final,
        "detalle_registros": [r.to_dict() for r in registros],
    }


def escribir_reporte(reporte: dict, ruta: str) -> None:
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

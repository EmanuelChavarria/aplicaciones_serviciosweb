"""
lectura.py

Se encarga unicamente de leer los archivos fuente y devolver los
registros crudos (sin transformar) junto con un identificador de
trazabilidad. No conoce nada del contrato institucional.
"""

import csv
import json
import os
from typing import List, Tuple

RegistroCrudo = Tuple[str, dict]  # (id_trazabilidad, dict_crudo)


def leer_proveedor_a(ruta: str) -> List[RegistroCrudo]:
    """
    Lee el archivo JSON del proveedor A.

    Maneja: archivo inexistente y JSON no interpretable devolviendo una
    lista vacia (el error queda registrado via excepcion controlada que
    el llamador puede loguear).
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No se encontro el archivo del proveedor A: {ruta}")

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"El archivo del proveedor A no contiene JSON valido: {exc}") from exc

    registros = contenido.get("records", [])
    resultado = []
    for i, registro in enumerate(registros):
        id_trazabilidad = registro.get("provider_record_id") or f"proveedor_a-pos-{i}"
        resultado.append((id_trazabilidad, registro))
    return resultado


def leer_proveedor_b(ruta: str) -> List[RegistroCrudo]:
    """
    Lee el archivo CSV del proveedor B (delimitado por ';').

    Maneja: archivo inexistente y filas defectuosas (numero de columnas
    distinto al del encabezado se registra como fila descartable, sin
    detener la ejecucion del programa).
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No se encontro el archivo del proveedor B: {ruta}")

    resultado = []
    with open(ruta, "r", encoding="utf-8", newline="") as f:
        lector = csv.reader(f, delimiter=";")
        try:
            encabezado = next(lector)
        except StopIteration:
            return resultado

        for i, fila in enumerate(lector):
            if len(fila) != len(encabezado):
                # Fila CSV defectuosa: se registra como error, no detiene el proceso.
                id_trazabilidad = f"proveedor_b-fila-{i + 2}"
                resultado.append(
                    (
                        id_trazabilidad,
                        {"__error_fila__": "numero de columnas no coincide con el encabezado"},
                    )
                )
                continue

            registro = dict(zip(encabezado, fila))
            id_trazabilidad = registro.get("record_code") or f"proveedor_b-fila-{i + 2}"
            resultado.append((id_trazabilidad, registro))

    return resultado

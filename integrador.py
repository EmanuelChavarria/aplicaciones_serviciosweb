"""
integrador.py

Punto de entrada del taller. Ejecuta el flujo completo de integracion:

    1. lee los datasets de ambos proveedores;
    2. normaliza cada registro al contrato institucional;
    3. valida localmente los registros normalizados;
    4. envia via HTTP los registros validos;
    5. interpreta las respuestas (incluyendo reintentos ante 5xx);
    6. consulta que quedo almacenado en la API;
    7. genera salida/normalizadas.json y salida/reporte.json.

Uso:
    python integrador.py
"""

import os
import sys

import requests

from contrato import Medicion, RegistroProcesado
from lectura import leer_proveedor_a, leer_proveedor_b
from normalizacion import normalizar_registro_a, normalizar_registro_b
from validacion import validar_medicion
from cliente_api import enviar_medicion, consultar_mediciones
from reporte import escribir_normalizadas, construir_reporte, escribir_reporte

# ---------------------------------------------------------------------------
# Configuracion (editar segun los datos asignados por el docente)
# ---------------------------------------------------------------------------
URL_BASE = "https://appsweb.quantaiot.co"
EQUIPO = "EQUIPO-09-APPSWEB"  

RUTA_PROVEEDOR_A = os.path.join("datos", "proveedor_a.json")
RUTA_PROVEEDOR_B = os.path.join("datos", "proveedor_b.csv")
RUTA_NORMALIZADAS = os.path.join("salida", "normalizadas.json")
RUTA_REPORTE = os.path.join("salida", "reporte.json")


def _cargar_fuentes():
    """
    Lee ambos datasets manejando de forma controlada archivo inexistente
    o contenido no interpretable. Devuelve una lista combinada de
    tuplas (id_trazabilidad, fuente, registro_crudo).
    """
    combinados = []

    try:
        registros_a = leer_proveedor_a(RUTA_PROVEEDOR_A)
        for id_trazabilidad, crudo in registros_a:
            combinados.append((id_trazabilidad, "proveedor_a", crudo))
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] No se pudo leer el proveedor A: {exc}", file=sys.stderr)

    try:
        registros_b = leer_proveedor_b(RUTA_PROVEEDOR_B)
        for id_trazabilidad, crudo in registros_b:
            combinados.append((id_trazabilidad, "proveedor_b", crudo))
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] No se pudo leer el proveedor B: {exc}", file=sys.stderr)

    return combinados


def _normalizar(id_trazabilidad: str, fuente: str, crudo: dict) -> RegistroProcesado:
    registro = RegistroProcesado(id_trazabilidad=id_trazabilidad, fuente=fuente)

    if fuente == "proveedor_a":
        medicion, error = normalizar_registro_a(crudo)
    else:
        medicion, error = normalizar_registro_b(crudo)

    if error is not None:
        registro.estado = "error_normalizacion"
        registro.detalle = error
        return registro

    registro.medicion = medicion
    registro.estado = "normalizado"
    return registro


def _validar(registro: RegistroProcesado) -> None:
    """Actualiza el estado del registro in-place segun la validacion local."""
    if registro.estado != "normalizado":
        return

    es_valido, motivo = validar_medicion(registro.medicion)
    if es_valido:
        registro.estado = "valido_local"
    else:
        registro.estado = "rechazado_local"
        registro.detalle = motivo


def _enviar(registro: RegistroProcesado, session: requests.Session) -> None:
    """Envia el registro a la API y actualiza su estado segun la respuesta."""
    if registro.estado != "valido_local":
        return

    resultado = enviar_medicion(URL_BASE, EQUIPO, registro.medicion.to_api_body(), session=session)
    registro.codigo_http = resultado.codigo_http
    registro.respuesta_api = resultado.cuerpo_respuesta
    registro.intentos = resultado.intentos
    registro.detalle = resultado.detalle

    if resultado.estado == "aceptado":
        registro.estado = "aceptado_api"
    elif resultado.estado == "rechazado_api":
        registro.estado = "rechazado_api"
    else:
        registro.estado = "error_comunicacion"


def main() -> None:
    print(f"Integrador iniciado. Equipo={EQUIPO} URL_BASE={URL_BASE}")

    crudos = _cargar_fuentes()
    print(f"Registros leidos: {len(crudos)}")

    registros = [_normalizar(id_t, fuente, crudo) for id_t, fuente, crudo in crudos]

    for registro in registros:
        _validar(registro)

    # Escribe normalizadas.json antes del envio: no depende de la disponibilidad de la API.
    escribir_normalizadas(registros, RUTA_NORMALIZADAS)
    print(f"Normalizadas escritas en {RUTA_NORMALIZADAS}")

    with requests.Session() as session:
        for registro in registros:
            _enviar(registro, session)

        print("Consultando mediciones almacenadas para el equipo...")
        resultado_consulta = consultar_mediciones(URL_BASE, EQUIPO, session=session)

    consulta_final = {
        "estado": resultado_consulta.estado,
        "codigo_http": resultado_consulta.codigo_http,
        "cuerpo": resultado_consulta.cuerpo_respuesta,
        "detalle": resultado_consulta.detalle,
    }

    reporte = construir_reporte(registros, EQUIPO, consulta_final)
    escribir_reporte(reporte, RUTA_REPORTE)
    print(f"Reporte escrito en {RUTA_REPORTE}")

    resumen = reporte["resumen"]
    print("\nResumen:")
    for clave, valor in resumen.items():
        print(f"  {clave}: {valor}")


if __name__ == "__main__":
    main()

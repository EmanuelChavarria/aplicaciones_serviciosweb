"""
cliente_api.py

Encapsula toda la comunicacion HTTP con la API institucional:
registro de mediciones (con reintentos controlados) y consulta final.

Reglas de reintento (definidas por el taller):
- 4xx: nunca se reintenta.
- 5xx / timeout / error de conexion: 1 intento inicial + hasta 2
  reintentos adicionales (maximo 3 intentos por registro).
"""

import time
from dataclasses import dataclass
from typing import Optional

import requests

MAX_INTENTOS = 3
ESPERA_ENTRE_REINTENTOS_SEG = 1.5
TIMEOUT_SEG = 10


@dataclass
class ResultadoEnvio:
    estado: str  # "aceptado" | "rechazado_api" | "error_comunicacion"
    codigo_http: Optional[int]
    cuerpo_respuesta: Optional[dict]
    intentos: int
    detalle: Optional[str] = None


def _intentar_parsear_json(respuesta: requests.Response) -> Optional[dict]:
    try:
        return respuesta.json()
    except ValueError:
        return None


def enviar_medicion(url_base: str, equipo: str, cuerpo: dict, session: Optional[requests.Session] = None) -> ResultadoEnvio:
    """
    Envia una medicion a POST /api/v1/mediciones aplicando la politica
    de reintentos del taller. No lanza excepciones: cualquier problema
    de comunicacion se traduce en un ResultadoEnvio con estado
    'error_comunicacion'.
    """
    http = session or requests
    url = f"{url_base.rstrip('/')}/api/v1/mediciones"
    headers = {"Content-Type": "application/json", "X-Equipo": equipo}

    ultimo_error = None
    for intento in range(1, MAX_INTENTOS + 1):
        try:
            respuesta = http.post(url, json=cuerpo, headers=headers, timeout=TIMEOUT_SEG)
        except (requests.Timeout, requests.ConnectionError) as exc:
            ultimo_error = str(exc)
            if intento < MAX_INTENTOS:
                time.sleep(ESPERA_ENTRE_REINTENTOS_SEG)
                continue
            return ResultadoEnvio(
                estado="error_comunicacion",
                codigo_http=None,
                cuerpo_respuesta=None,
                intentos=intento,
                detalle=f"Fallo de comunicacion tras {intento} intentos: {ultimo_error}",
            )
        except requests.RequestException as exc:
            # Cualquier otro error inesperado de la libreria tampoco debe tumbar el programa.
            return ResultadoEnvio(
                estado="error_comunicacion",
                codigo_http=None,
                cuerpo_respuesta=None,
                intentos=intento,
                detalle=f"Error inesperado de comunicacion: {exc}",
            )

        cuerpo_json = _intentar_parsear_json(respuesta)

        if respuesta.status_code == 201:
            return ResultadoEnvio("aceptado", respuesta.status_code, cuerpo_json, intento)

        if respuesta.status_code in (400, 409, 422):
            # 4xx: no se reintenta.
            return ResultadoEnvio("rechazado_api", respuesta.status_code, cuerpo_json, intento)

        if 500 <= respuesta.status_code < 600:
            if intento < MAX_INTENTOS:
                time.sleep(ESPERA_ENTRE_REINTENTOS_SEG)
                continue
            return ResultadoEnvio(
                estado="error_comunicacion",
                codigo_http=respuesta.status_code,
                cuerpo_respuesta=cuerpo_json,
                intentos=intento,
                detalle=f"Servidor devolvio {respuesta.status_code} tras {intento} intentos",
            )

        # Codigo HTTP no contemplado explicitamente por el contrato: se
        # trata como respuesta no exitosa, sin reintentar, para no
        # asumir semantica que el contrato no define.
        return ResultadoEnvio(
            estado="rechazado_api",
            codigo_http=respuesta.status_code,
            cuerpo_respuesta=cuerpo_json,
            intentos=intento,
            detalle=f"Codigo HTTP inesperado: {respuesta.status_code}",
        )

    # No deberia llegar aqui, pero se deja como salvaguarda.
    return ResultadoEnvio("error_comunicacion", None, None, MAX_INTENTOS, ultimo_error)


def consultar_mediciones(url_base: str, equipo: str, session: Optional[requests.Session] = None) -> ResultadoEnvio:
    """Consulta GET /api/v1/mediciones?equipo=<equipo>."""
    http = session or requests
    url = f"{url_base.rstrip('/')}/api/v1/mediciones"

    try:
        respuesta = http.get(url, params={"equipo": equipo}, timeout=TIMEOUT_SEG)
    except (requests.Timeout, requests.ConnectionError) as exc:
        return ResultadoEnvio("error_comunicacion", None, None, 1, f"Fallo de comunicacion: {exc}")
    except requests.RequestException as exc:
        return ResultadoEnvio("error_comunicacion", None, None, 1, f"Error inesperado: {exc}")

    cuerpo_json = _intentar_parsear_json(respuesta)

    if respuesta.status_code == 200:
        return ResultadoEnvio("aceptado", 200, cuerpo_json, 1)

    return ResultadoEnvio(
        "rechazado_api",
        respuesta.status_code,
        cuerpo_json,
        1,
        f"Consulta devolvio codigo {respuesta.status_code}",
    )

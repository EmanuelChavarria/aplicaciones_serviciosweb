import pytest

import cliente_api
from cliente_api import enviar_medicion


@pytest.fixture(autouse=True)
def _sin_espera_entre_reintentos(monkeypatch):
    """Evita que las pruebas esperen tiempo real entre reintentos."""
    monkeypatch.setattr(cliente_api, "ESPERA_ENTRE_REINTENTOS_SEG", 0)


class _RespuestaFalsa:
    def __init__(self, status_code, cuerpo=None):
        self.status_code = status_code
        self._cuerpo = cuerpo or {}

    def json(self):
        return self._cuerpo


class _SesionFalsa:
    """Simula requests.Session sin hacer ninguna llamada de red real."""

    def __init__(self, respuestas):
        # 'respuestas' es una lista de _RespuestaFalsa que se devuelven en orden.
        self._respuestas = list(respuestas)
        self.llamadas = 0

    def post(self, url, json=None, headers=None, timeout=None):
        self.llamadas += 1
        return self._respuestas[self.llamadas - 1]


def test_envio_exitoso_no_reintenta():
    sesion = _SesionFalsa([_RespuestaFalsa(201, {"id": "srv-1"})])

    resultado = enviar_medicion("https://ejemplo.test", "EQUIPO_X", {"ciudad": "Medellin"}, session=sesion)

    assert resultado.estado == "aceptado"
    assert resultado.intentos == 1
    assert sesion.llamadas == 1


def test_error_4xx_no_se_reintenta():
    sesion = _SesionFalsa([_RespuestaFalsa(422, {"error": "dato invalido"})])

    resultado = enviar_medicion("https://ejemplo.test", "EQUIPO_X", {"ciudad": ""}, session=sesion)

    assert resultado.estado == "rechazado_api"
    assert resultado.codigo_http == 422
    assert sesion.llamadas == 1  # nunca reintenta ante 4xx


def test_error_5xx_reintenta_hasta_tres_intentos_y_luego_falla():
    sesion = _SesionFalsa(
        [
            _RespuestaFalsa(500),
            _RespuestaFalsa(503),
            _RespuestaFalsa(500),
        ]
    )

    resultado = enviar_medicion("https://ejemplo.test", "EQUIPO_X", {"ciudad": "Cali"}, session=sesion)

    assert resultado.estado == "error_comunicacion"
    assert resultado.intentos == 3
    assert sesion.llamadas == 3  # 1 intento inicial + 2 reintentos, maximo permitido


def test_error_5xx_se_recupera_en_un_reintento():
    sesion = _SesionFalsa(
        [
            _RespuestaFalsa(500),
            _RespuestaFalsa(201, {"id": "srv-2"}),
        ]
    )

    resultado = enviar_medicion("https://ejemplo.test", "EQUIPO_X", {"ciudad": "Bogota"}, session=sesion)

    assert resultado.estado == "aceptado"
    assert resultado.intentos == 2
    assert sesion.llamadas == 2

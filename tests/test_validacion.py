from contrato import Medicion
from validacion import validar_medicion


def _medicion_base(**overrides) -> Medicion:
    base = dict(
        ciudad="Medellin",
        pais="CO",
        latitud=6.25,
        longitud=-75.56,
        temperatura_c=20.0,
        humedad=80.0,
        viento_kmh=18.0,
        fecha_hora="2026-09-01T00:00:00-05:00",
        origen="proveedor_a",
    )
    base.update(overrides)
    return Medicion(**base)


def test_registro_valido_pasa_la_validacion():
    medicion = _medicion_base()
    es_valida, motivo = validar_medicion(medicion)
    assert es_valida is True
    assert motivo is None


def test_registro_invalido_por_humedad_fuera_de_rango():
    """Humedad de 117.5 (visto en los datos reales) debe rechazarse."""
    medicion = _medicion_base(humedad=117.5)
    es_valida, motivo = validar_medicion(medicion)
    assert es_valida is False
    assert "humedad" in motivo


def test_caso_limite_humedad_en_los_bordes_del_rango():
    """0 y 100 son los limites inclusivos permitidos por el contrato."""
    medicion_min = _medicion_base(humedad=0)
    medicion_max = _medicion_base(humedad=100)

    es_valida_min, _ = validar_medicion(medicion_min)
    es_valida_max, _ = validar_medicion(medicion_max)

    assert es_valida_min is True
    assert es_valida_max is True

    # Justo fuera del limite superior debe rechazarse.
    medicion_fuera = _medicion_base(humedad=100.01)
    es_valida_fuera, motivo_fuera = validar_medicion(medicion_fuera)
    assert es_valida_fuera is False
    assert "humedad" in motivo_fuera

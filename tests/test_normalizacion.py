from normalizacion import normalizar_registro_a, normalizar_registro_b


def test_normalizacion_correcta_proveedor_a():
    """Un registro bien formado del proveedor A se transforma sin errores."""
    crudo = {
        "provider_record_id": "A-TEST",
        "station": {"city_name": "Medellin", "country_code": "CO"},
        "location": {"lat": 6.25, "lon": -75.56},
        "measurements": {
            "temperature_f": 68.0,
            "relative_humidity": 80.0,
            "wind_speed_ms": 5.0,
        },
        "observed_at": "2026-09-01T00:00:00-05:00",
        "source": "weather_provider_a",
    }

    medicion, error = normalizar_registro_a(crudo)

    assert error is None
    assert medicion.ciudad == "Medellin"
    assert medicion.pais == "CO"
    assert medicion.origen == "proveedor_a"
    assert medicion.fecha_hora == "2026-09-01T00:00:00-05:00"


def test_conversion_unidades_temperatura_y_viento():
    """68F deben ser 20C y 5 m/s deben ser 18 km/h (conversion de unidades)."""
    crudo = {
        "provider_record_id": "A-CONV",
        "station": {"city_name": "Cali", "country_code": "CO"},
        "location": {"lat": 3.45, "lon": -76.53},
        "measurements": {
            "temperature_f": 68.0,
            "relative_humidity": 50.0,
            "wind_speed_ms": 5.0,
        },
        "observed_at": "2026-09-01T00:00:00-05:00",
        "source": "weather_provider_a",
    }

    medicion, error = normalizar_registro_a(crudo)

    assert error is None
    assert medicion.temperatura_c == 20.0
    assert medicion.viento_kmh == 18.0


def test_error_de_normalizacion_proveedor_b_temperatura_no_numerica():
    """Un valor no convertible a numero debe reportarse como error de normalizacion."""
    crudo = {
        "record_code": "B-TEST",
        "municipality": "Bogota",
        "country": "CO",
        "latitude_deg": "4.6",
        "longitude_deg": "-74.1",
        "temp_celsius": "error",
        "humidity_pct": "60",
        "wind_kmh": "10",
        "measurement_time": "01/09/2026 06:00",
        "origin_code": "PB",
    }

    medicion, error = normalizar_registro_b(crudo)

    assert medicion is None
    assert error is not None
    assert "temperatura_c" in error

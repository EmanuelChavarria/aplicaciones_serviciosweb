"""Pruebas de los endpoints HTTP (evidencias 8 a 16 y códigos 200/400/404/422)."""

from tests.conftest import insertar_medicion, utc


def sembrar(db):
    """Tres lecturas (cada una con temperature y humidity) a las 10:00, 10:05 y 10:10 UTC."""
    ids = {}
    for i, minuto in enumerate((0, 5, 10)):
        ts = utc(2026, 10, 7, 10, minuto)
        ids[f"t{i}"] = insertar_medicion(db, 1, f"2{i}.5", ts).id
        ids[f"h{i}"] = insertar_medicion(db, 2, f"{50 + i}", ts).id
    return ids


# --- Catálogo -----------------------------------------------------------------
def test_catalogo_sensores_y_magnitudes(client):
    r = client.get("/sensores")
    assert r.status_code == 200 and len(r.json()) == 3

    r = client.get("/sensores/1")
    assert r.status_code == 200
    assert r.json()["codigo"] == "TEST-001"
    assert r.json()["fecha_registro"].endswith("(UTC-05:00)")

    r = client.get("/sensores/por-codigo/TEST-001")
    assert r.status_code == 200 and r.json()["id"] == 1

    r = client.get("/sensores/1/magnitudes")
    assert r.status_code == 200
    assert [m["magnitud"] for m in r.json()] == ["temperature", "humidity"]

    r = client.get("/sensor-magnitudes/1")
    assert r.status_code == 200 and r.json()["unidad"] == "C"


def test_catalogo_404(client):
    assert client.get("/sensores/999").status_code == 404
    assert client.get("/sensores/por-codigo/NOPE").status_code == 404
    assert client.get("/sensores/999/magnitudes").status_code == 404
    assert client.get("/sensor-magnitudes/999").status_code == 404


# --- Evidencias 8 y 9: consulta por ID ----------------------------------------
def test_08_medicion_por_id_existente_con_hora_colombia(client, db):
    ids = sembrar(db)
    r = client.get(f"/mediciones/{ids['t0']}")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["sensor_codigo"] == "TEST-001" and cuerpo["magnitud"] == "temperature"
    assert cuerpo["valor"] == 20.5
    # 10:00 UTC == 05:00 en Colombia
    assert cuerpo["timestamp_colombia"] == "2026-10-07 05:00:00 (UTC-05:00)"


def test_09_medicion_por_id_inexistente_404(client):
    assert client.get("/mediciones/123456").status_code == 404


# --- Evidencia 10: histórico ----------------------------------------------------
def test_10_historico_completo_mas_reciente_primero(client, db):
    sembrar(db)
    r = client.get("/sensores/1/mediciones")
    assert r.status_code == 200
    assert len(r.json()) == 6
    assert r.json()[0]["timestamp_colombia"] == "2026-10-07 05:10:00 (UTC-05:00)"


# --- Evidencia 11: rango de fechas ----------------------------------------------
def test_11_rango_de_fechas_con_zona_explicita(client, db):
    sembrar(db)
    r = client.get(
        "/sensores/1/mediciones",
        params={"desde": "2026-10-07T10:03:00Z", "hasta": "2026-10-07T10:07:00Z"},
    )
    assert r.status_code == 200
    assert {m["timestamp_colombia"] for m in r.json()} == {"2026-10-07 05:05:00 (UTC-05:00)"}


def test_11_rango_sin_zona_se_interpreta_como_hora_de_colombia(client, db):
    sembrar(db)
    # 05:03 a 05:07 hora Colombia == 10:03 a 10:07 UTC -> solo la lectura de las 05:05
    r = client.get(
        "/sensores/1/mediciones",
        params={"desde": "2026-10-07T05:03:00", "hasta": "2026-10-07T05:07:00"},
    )
    assert r.status_code == 200 and len(r.json()) == 2


# --- Evidencia 12: desde > hasta ------------------------------------------------
def test_12_desde_mayor_que_hasta_400(client, db):
    sembrar(db)
    r = client.get(
        "/sensores/1/mediciones",
        params={"desde": "2026-10-07T12:00:00Z", "hasta": "2026-10-07T10:00:00Z"},
    )
    assert r.status_code == 400


# --- Evidencia 13: validación HTTP -> 422 ---------------------------------------
def test_13_validacion_http_422(client):
    assert client.get("/sensores/abc").status_code == 422
    assert client.get("/sensores/1/mediciones", params={"limit": 0}).status_code == 422
    assert client.get("/sensores/1/mediciones", params={"limit": "x"}).status_code == 422
    assert client.get("/sensores/1/mediciones", params={"desde": "no-es-fecha"}).status_code == 422
    assert client.get("/mediciones/abc").status_code == 422


# --- Evidencia 14: última medición ----------------------------------------------
def test_14_ultima_medicion(client, db):
    sembrar(db)
    r = client.get("/sensores/1/ultima-medicion")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["timestamp_colombia"] == "2026-10-07 05:10:00 (UTC-05:00)"
    assert {m["magnitud"]: m["valor"] for m in cuerpo["mediciones"]} == {
        "temperature": 22.5,
        "humidity": 52.0,
    }


def test_14_ultima_medicion_sin_datos_404(client):
    assert client.get("/sensores/1/ultima-medicion").status_code == 404
    assert client.get("/sensores/999/ultima-medicion").status_code == 404


# --- Evidencia 15: últimas N ----------------------------------------------------
def test_15_limit_devuelve_las_ultimas_n(client, db):
    sembrar(db)
    r = client.get("/sensores/1/mediciones", params={"limit": 2})
    assert r.status_code == 200 and len(r.json()) == 2
    assert {m["timestamp_colombia"] for m in r.json()} == {"2026-10-07 05:10:00 (UTC-05:00)"}


# --- Evidencia 16: filtro por magnitud ------------------------------------------
def test_16_filtro_por_magnitud_y_combinacion_de_filtros(client, db):
    sembrar(db)
    r = client.get("/sensores/1/mediciones", params={"magnitud": "temperature"})
    assert r.status_code == 200 and len(r.json()) == 3
    assert {m["magnitud"] for m in r.json()} == {"temperature"}

    r = client.get(
        "/sensores/1/mediciones",
        params={
            "magnitud": "temperature",
            "desde": "2026-10-07T10:00:00Z",
            "hasta": "2026-10-07T10:10:00Z",
            "limit": 2,
        },
    )
    assert r.status_code == 200
    assert [m["valor"] for m in r.json()] == [22.5, 21.5]  # las 2 últimas, de más nueva a más vieja


def test_16_magnitud_que_el_sensor_no_mide_404(client, db):
    sembrar(db)
    assert client.get("/sensores/1/mediciones", params={"magnitud": "co2"}).status_code == 404


def test_historico_de_sensor_inexistente_404(client):
    assert client.get("/sensores/999/mediciones").status_code == 404

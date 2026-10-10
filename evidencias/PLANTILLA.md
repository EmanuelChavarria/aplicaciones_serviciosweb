# Evidencias — Taller 2

Para cada prueba: ejecuta el comando, guarda una captura (o el texto de la salida) en esta carpeta con el nombre indicado y completa las columnas **Resultado obtenido** y **Registro**.

Las pruebas automáticas (`pytest -v`) reproducen las mismas situaciones sin broker y sirven como respaldo, pero la guía pide evidencia con **tu sensor, tu broker y tu PostgreSQL**.

> Consejo: levanta la app con `uvicorn app.main:app` y deja correr 20+ minutos. Las líneas `ACEPTADO` / `RECHAZADO` quedan en `logs/app.log`; copia las relevantes a `evidencias/log_mqtt.txt`.

## Evidencias MQTT (sin código HTTP)

| # | Prueba | Cómo evidenciarla | Archivo y función | Resultado esperado | Resultado obtenido / registro |
|---|---|---|---|---|---|
| 1 | Recepción MQTT | Línea `Mensaje recibido en iot/sensors/<TU-SENSOR>/data` en el log | `app/mqtt/client.py` → `on_message` | Mensaje del tópico asignado | _completar_ |
| 2 | Medición válida | `SELECT * FROM mediciones ORDER BY id DESC LIMIT 5;` + línea `ACEPTADO` | `app/services/ingesta.py` → `procesar_mensaje`; `app/crud/medicion.py` → `create_many` | Una fila por magnitud, mismo `timestamp_utc` | _completar_ |
| 3 | Sensor inexistente | Línea `RECHAZADO [SENSOR_INEXISTENTE]` + `COUNT(*)` sin cambios | `app/services/ingesta.py` → `procesar_mensaje` (paso 3) | Rechazado, no se guarda | _completar_ |
| 4 | Unidad incorrecta | Línea `RECHAZADO [UNIDAD_INVALIDA]` | `app/services/ingesta.py` → `procesar_mensaje` (paso 7) | Rechazado | _completar_ |
| 5 | Tipo de dato incorrecto | Línea `RECHAZADO [TIPO_DATO_INVALIDO]` | `app/schemas/medicion.py` → `MedidaPayload`; `_clasificar_error_pydantic` | Rechazado | _completar_ |
| 6 | Magnitud incorrecta | Línea `RECHAZADO [MAGNITUD_INVALIDA]` | `app/services/ingesta.py` → `procesar_mensaje` (paso 6) | Rechazado | _completar_ |
| 7 | Timestamp inválido | Línea `RECHAZADO [TIMESTAMP_INVALIDO]` | `app/schemas/medicion.py` → `PayloadMQTT._timestamp_utc` | Rechazado | _completar_ |

> Los mensajes inválidos los publica el servicio MQTT del docente de forma intencional. Si en tus 20 minutos no aparece alguno de los casos, indícalo aquí y apóyate en la prueba automática correspondiente (`tests/test_ingesta.py`).

## Evidencias HTTP

Sustituye `{id}` por ids reales de tu base. Con la app corriendo: `http://127.0.0.1:8000`.

| # | Prueba | Comando | Archivo y función | Esperado | Resultado obtenido |
|---|---|---|---|---|---|
| 8 | Consulta por ID existente | `curl -i http://127.0.0.1:8000/mediciones/{id}` | `app/api/medicion.py` → `obtener_medicion` | `200` | _completar_ |
| 9 | Consulta por ID inexistente | `curl -i http://127.0.0.1:8000/mediciones/99999999` | `app/api/medicion.py` → `obtener_medicion` | `404` | _completar_ |
| 10 | Consulta histórica | `curl -i http://127.0.0.1:8000/sensores/{id}/mediciones` | `app/api/medicion.py` → `listar_mediciones_de_sensor`; `app/crud/medicion.py` → `list_by_sensor` | `200` + lista | _completar_ |
| 11 | Rango de fechas | `curl -i "http://127.0.0.1:8000/sensores/{id}/mediciones?desde=2026-10-10T10:00:00&hasta=2026-10-10T10:30:00"` | ídem | `200` filtrado | _completar_ |
| 12 | `desde > hasta` | `curl -i "http://127.0.0.1:8000/sensores/{id}/mediciones?desde=2026-10-10T12:00:00&hasta=2026-10-10T10:00:00"` | `app/api/medicion.py` → `listar_mediciones_de_sensor` | `400` | _completar_ |
| 13 | Validación HTTP incorrecta | `curl -i http://127.0.0.1:8000/sensores/abc` (o `?limit=0`) | FastAPI + `Query(ge=1)` en `app/api/medicion.py` | `422` | _completar_ |
| 14 | Última medición | `curl -i http://127.0.0.1:8000/sensores/{id}/ultima-medicion` | `app/api/medicion.py` → `obtener_ultima_medicion`; `app/crud/medicion.py` → `ultima_by_sensor` | `200` | _completar_ |
| 15 | Últimas N | `curl -i "http://127.0.0.1:8000/sensores/{id}/mediciones?limit=10"` | `app/crud/medicion.py` → `list_by_sensor` | `200`, ≤10 filas | _completar_ |
| 16 | Filtro por magnitud | `curl -i "http://127.0.0.1:8000/sensores/{id}/mediciones?magnitud=temperature"` | ídem | `200`, una sola magnitud | _completar_ |

## Evidencias de diseño

| # | Prueba | Cómo evidenciarla | Archivo | Resultado obtenido |
|---|---|---|---|---|
| 17 | Claves foráneas | Captura de `\d mediciones` en `psql` y de `app/models/*.py` mostrando `ForeignKey`/`relationship`; respuesta de `GET /mediciones/{id}` con `sensor_codigo` y `magnitud` | `app/models/medicion.py`, `app/models/sensor_magnitud.py` | _completar_ |
| 18 | Separación de responsabilidades | Árbol de carpetas (`tree app`) y la tabla de la sección 5 del README | `app/` | _completar_ |

## Códigos HTTP demostrados

- [ ] 200 (pruebas 8, 10, 11, 14, 15, 16)
- [ ] 400 (prueba 12)
- [ ] 404 (prueba 9)
- [ ] 422 (prueba 13)

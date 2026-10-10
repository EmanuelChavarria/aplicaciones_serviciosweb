# Evidencias — Taller 2

Sensor **WQ-001** (id `9` en la BD) · tópico `iot/sensors/WQ-001/data` · broker `emqx.coriotlab.co:1883`

**Recolección real:** del 2026-10-10 13:10:20 al 15:07:45 (hora Colombia) → **1 h 57 min** (la guía exige mínimo 20 min).
1147 mensajes recibidos · 1089 aceptados (2178 filas en `mediciones`) · 58 rechazados.

| # | Prueba | Estado | Evidencia |
|---|---|:-:|---|
| 1 | Recepción MQTT | ✅ | [`log_mqtt.txt`](log_mqtt.txt) |
| 2 | Medición válida | ✅ | [`log_mqtt.txt`](log_mqtt.txt), capturas [14](capturas/14_ultima_medicion.png) y [10](capturas/10_consulta_historica.png) |
| 3 | Sensor inexistente 
| 4 | Unidad incorrecta | ✅ | [`log_mqtt.txt`](log_mqtt.txt) |
| 5 | Tipo de dato incorrecto | ✅ | [`log_mqtt.txt`](log_mqtt.txt) |
| 6 | Magnitud incorrecta | ✅ | [`log_mqtt.txt`](log_mqtt.txt) |
| 7 | Timestamp inválido | ✅ | [`log_mqtt.txt`](log_mqtt.txt) |
| 8 | Consulta por ID existente | ⚠️ | [captura 08](capturas/08_consulta_id_existente.png) (es de otro sensor, ver detalle) |
| 9 | Consulta por ID inexistente (404) | ✅ | [captura 09](capturas/09_consulta_id_inexistente_404.png) |
| 10 | Consulta histórica | ✅ | [captura 10](capturas/10_consulta_historica.png) |
| 11 | Rango de fechas | ✅ | [captura 11](capturas/11_consulta_rango_fechas.png) |
| 12 | `desde > hasta` (400) | [captura 12](capturas/12_desde_mayor_que_hasta_400.png) |
| 13 | Validación HTTP (422) | [captura 13](capturas/13_validacion_http_incorrecta.png) |
| 14 | Última medición | ✅ | [captura 14](capturas/14_ultima_medicion.png) |
| 15 | Últimas N (`limit`) | ✅ | [captura 15](capturas/15_ultimas_n_limit.png) |
| 16 | Filtro por magnitud | ✅ | [captura 16](capturas/16_filtro_magnitud.png) |
| 17 | Claves foráneas | [captura 17](capturas/17_Relacion_de_claves_foraneas.png) |
| 18 | Separación de responsabilidades | ✅ | [`arbol_app.txt`](arbol_app.txt) + sección 5 del README |

**Códigos HTTP demostrados:** 200 ✅ · 400 ⚠️ · 404 ✅ · 422 ❌

---

## Evidencias MQTT (sin código HTTP)

Los mensajes inválidos los publica el servicio del docente de forma intencional. Las líneas completas están en [`log_mqtt.txt`](log_mqtt.txt).

### 1. Recepción MQTT
- **Entrada:** mensaje publicado en `iot/sensors/WQ-001/data`.
- **Resultado:** `Mensaje recibido en iot/sensors/WQ-001/data: {"sensor_id": "WQ-001", "timestamp": "2026-10-10T18:10:20Z", ...}` (13:10:20, hora Colombia).
- **Archivo y función:** `app/mqtt/client.py` → `on_message`.
- **Explicación:** el cliente se conecta, se suscribe al tópico asignado y registra cada mensaje recibido antes de delegarlo al servicio de ingesta.

### 2. Medición válida
- **Entrada:** `temperature = 26.74 C` y `ph = 7.33 pH`, timestamp `2026-10-10T18:10:20Z`.
- **Resultado:** `ACEPTADO [OK] 2 medición(es) del sensor 'WQ-001' guardadas`. Una fila por magnitud con el mismo `timestamp_utc`; se ve en la [última medición](capturas/14_ultima_medicion.png) (ids 109529 y 109530, mismo timestamp).
- **Archivo y función:** `app/services/ingesta.py` → `procesar_mensaje`; `app/crud/medicion.py` → `create_many`.
- **Explicación:** si todo el payload es válido se guardan todas las magnitudes en una sola transacción.

### 3. Sensor inexistente —
- **Situación:** en las 1 h 57 min de recolección **no llegó ningún mensaje con `SENSOR_INEXISTENTE`** (0 ocurrencias en `logs/app.log`).
- **Respaldo:** `tests/test_ingesta.py::test_03_sensor_inexistente`. Ejecutar `pytest -v -k test_03` y adjuntar la captura de la salida.
- **Archivo y función:** `app/services/ingesta.py` → `procesar_mensaje` (paso 3).

### 4. Unidad incorrecta (11 casos en la recolección)
- **Entrada:** `temperature` con unidad `INVALID_UNIT` (13:12:10).
- **Resultado:** `RECHAZADO [UNIDAD_INVALIDA] 'temperature' debe venir en 'C', llegó 'INVALID_UNIT'`.
- **Archivo y función:** `app/services/ingesta.py` → `procesar_mensaje` (paso 7).

### 5. Tipo de dato incorrecto (17 casos)
- **Entrada:** `ph.value` como texto `"6.28"` en lugar de número (13:13:35).
- **Resultado:** `RECHAZADO [TIPO_DATO_INVALIDO] measurements.ph.value.int: Input should be a valid integer`.
- **Archivo y función:** `app/schemas/medicion.py` → `MedidaPayload`; `app/services/ingesta.py` → `_clasificar_error_pydantic`.

### 6. Magnitud incorrecta (10 casos)
- **Entrada:** magnitud `humidity` que WQ-001 no mide (13:13:45).
- **Resultado:** `RECHAZADO [MAGNITUD_INVALIDA] el sensor 'WQ-001' no mide la magnitud 'humidity'`.
- **Archivo y función:** `app/services/ingesta.py` → `procesar_mensaje` (paso 6).

### 7. Timestamp inválido (9 casos)
- **Entrada:** `"timestamp": "not-a-timestamp"` (13:56:35).
- **Resultado:** `RECHAZADO [TIMESTAMP_INVALIDO] timestamp: Value error, timestamp debe ser texto ISO 8601 con zona, p. ej. 2026-10-07T16:25:30Z`.
- **Archivo y función:** `app/schemas/medicion.py` → `PayloadMQTT._timestamp_utc`.

### Casos adicionales observados
- `ESTRUCTURA_INVALIDA` (7): falta el campo obligatorio `unit` (13:23:30).
- `VALOR_FUERA_DE_RANGO` (4): `temperature = 999999.0` fuera de `[0, 50] C`; `ph = 999999.0` fuera de `[0, 14] pH`.

### Comprobación de que lo inválido no se guardó
En el log, ninguno de los 50 timestamps de mensajes rechazados aparece luego como `ACEPTADO`. Para evidenciarlo contra la base, consultar el instante del caso 4 (18:12:10Z = 13:12:10 hora Colombia):

```bash
curl -i "http://127.0.0.1:8000/sensores/9/mediciones?desde=2026-10-10T13:12:10&hasta=2026-10-10T13:12:10"
```
Resultado esperado: `200` con lista vacía `[]`. ❌ *Pendiente de capturar.*

---

## Evidencias HTTP

### 8. Consulta por ID existente — ⚠️
- **Entrada:** `GET /mediciones/10` → `200`.
- **Resultado:** `{"id":10,"sensor_magnitud_id":6,"sensor_id":2,"sensor_codigo":"AQ-002","magnitud":"pm1_0","unidad":"ug/m3","valor":35.1,"timestamp_colombia":"2026-10-08 01:35:13 (UTC-05:00)", ...}`
- **Ajuste recomendado:** esa medición es del sensor **AQ-002**, no del asignado. Repetir con una medición de WQ-001, por ejemplo `GET /mediciones/109121` (aparece en la [captura 10](capturas/10_consulta_historica.png): `ph = 7.54`, `2026-10-10 14:21:00 (UTC-05:00)`).
- **Archivo y función:** `app/api/medicion.py` → `obtener_medicion`.

### 9. Consulta por ID inexistente — ✅
- **Entrada:** `GET /mediciones/99999999` → **`404`**, `{"detail": "No existe la medición con id 99999999"}`.
- **Archivo y función:** `app/api/medicion.py` → `obtener_medicion`.

### 10. Consulta histórica — ✅
- **Entrada:** `GET /sensores/9/mediciones` → `200`, lista ordenada de la más reciente a la más antigua, con `timestamp_colombia` en formato `2026-10-10 14:21:00 (UTC-05:00)`.
- **Archivo y función:** `app/api/medicion.py` → `listar_mediciones_de_sensor`; `app/crud/medicion.py` → `list_by_sensor`.

### 11. Rango de fechas — ✅
- **Entrada:** `GET /sensores/9/mediciones?desde=2026-10-10T13:15:00&hasta=2026-10-10T13:20:00` → `200`.
- **Resultado:** solo mediciones entre 13:15 y 13:20 (la primera es `13:20:00`). Sin zona horaria, las fechas se interpretan como hora de Colombia.
- **Archivo y función:** `app/crud/medicion.py` → `list_by_sensor`.

### 12. `desde > hasta` — ⚠️
- **Resultado:** **`400`**, `{"detail": "'desde' no puede ser posterior a 'hasta'"}`.
- **Ajuste recomendado:** la captura no muestra la URL consultada. Repetirla incluyendo el bloque *Curl / Request URL*, o con `curl -i`:
  `curl -i "http://127.0.0.1:8000/sensores/9/mediciones?desde=2026-10-10T14:00:00&hasta=2026-10-10T13:00:00"`
- **Archivo y función:** `app/api/medicion.py` → `listar_mediciones_de_sensor`.

### 13. Validación HTTP incorrecta —
- **Comando sugerido:** `curl -i "http://127.0.0.1:8000/sensores/9/mediciones?limit=0"` (o `/sensores/abc`) → **`422`**.
- **Archivo y función:** FastAPI + `Query(None, ge=1, le=10000)` en `app/api/medicion.py` → `listar_mediciones_de_sensor`.

### 14. Última medición — ✅
- **Entrada:** `GET /sensores/9/ultima-medicion` → `200`.
- **Resultado:** `timestamp_colombia = 2026-10-10 14:28:05 (UTC-05:00)` con las dos magnitudes del mismo payload: `ph = 6.18` (id 109530) y `temperature = 18.75` (id 109529).
- **Archivo y función:** `app/api/medicion.py` → `obtener_ultima_medicion`; `app/crud/medicion.py` → `ultima_by_sensor`.

### 15. Últimas N — ✅
- **Entrada:** `GET /sensores/9/mediciones?limit=10` → `200`, exactamente 10 filas (ids 109286 … 109265, de 14:23:50 a 14:23:30).
- **Archivo y función:** `app/crud/medicion.py` → `list_by_sensor`.

### 16. Filtro por magnitud — ✅
- **Entrada:** `GET /sensores/9/mediciones?magnitud=temperature` → `200`, todas las filas con `magnitud = "temperature"` y `unidad = "C"`.
- **Archivo y función:** `app/crud/medicion.py` → `list_by_sensor`.

---

## Evidencias de diseño

### 17. Claves foráneas —
- **Implementación:**
  - `mediciones.sensor_magnitud_id → sensor_magnitudes.id` (`app/models/medicion.py`)
  - `sensor_magnitudes.sensor_id → sensores.id` (`app/models/sensor_magnitud.py`)
  - Ambas con `ON UPDATE CASCADE ON DELETE RESTRICT` y `relationship(...)` en los dos sentidos.
- **Se ve en las respuestas:** cada medición devuelve `sensor_magnitud_id`, `sensor_id`, `sensor_codigo` y `magnitud`, obtenidos navegando las relaciones.
- **Pendiente:** captura de `\d mediciones` en `psql` mostrando la restricción de clave foránea.

### 18. Separación de responsabilidades — ✅
- **Evidencia:** [`arbol_app.txt`](arbol_app.txt) (estructura real de `app/`) y la tabla de responsabilidades de la sección 5 del README.

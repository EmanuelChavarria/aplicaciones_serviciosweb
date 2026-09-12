# ANALISIS.md — Taller 1: Integración de datos entre aplicaciones

## Tabla de correspondencia de campos

| Contrato institucional | Proveedor A (JSON)                         | Proveedor B (CSV)          | Transformación aplicada |
|---|---|---|---|
| `ciudad`        | `station.city_name`                | `municipality`      | Copia directa (string) |
| `pais`          | `station.country_code`             | `country`           | Copia directa (se conservó el código, ej. `CO`; el contrato solo exige "no vacío" y no define un formato específico) |
| `latitud`       | `location.lat` (float)             | `latitude_deg` (string) | Cast a `float` |
| `longitud`      | `location.lon` (float)             | `longitude_deg` (string)| Cast a `float` |
| `temperatura_c` | `measurements.temperature_f` (°F)  | `temp_celsius` (°C, string) | A: `(F-32)*5/9`. B: solo cast a `float` |
| `humedad`       | `measurements.relative_humidity` (%)| `humidity_pct` (%, string) | Cast a `float` |
| `viento_kmh`    | `measurements.wind_speed_ms` (m/s) | `wind_kmh` (km/h, string) | A: `m/s * 3.6`. B: solo cast a `float` |
| `fecha_hora`    | `observed_at` (ISO 8601 con offset)| `measurement_time` (`DD/MM/YYYY HH:MM`) | A: se valida y re-serializa. B: se parsea y se le agrega el offset `-05:00` (ver supuesto abajo) |
| `origen`        | constante `proveedor_a` (deducida de `source`) | `origin_code` = `PB` → constante `proveedor_b` | Mapeo a valor institucional fijo |
| Trazabilidad    | `provider_record_id`               | `record_code`       | Se usa solo para evidencia/reporte, no se envía en el body |

## 1. Diferencias entre los contratos de los proveedores

- **Formato de archivo**: A es JSON anidado (objetos `station`, `location`, `measurements`); B es CSV plano delimitado por `;`.
- **Unidades**: A entrega temperatura en Fahrenheit y viento en m/s; B ya entrega Celsius y km/h, coincidiendo con el contrato institucional.
- **Fechas**: A usa ISO 8601 con offset (`-05:00`); B usa `DD/MM/YYYY HH:MM` sin zona horaria explícita.
- **Identificación de origen**: A lo indica en `source` (`weather_provider_a`); B lo indica con un código corto (`PB`) que debe mapearse al valor institucional.
- **Calidad de datos**: ambos proveedores presentan registros incompletos o corruptos, pero de forma distinta: A tiene valores `null`/`"N/A"`/claves ausentes; B tiene celdas vacías o literal `"error"`/fechas con valores fuera de rango (`31/13/2026 28:75`).

## 2. Transformaciones necesarias

- Conversión de unidades: Fahrenheit→Celsius y m/s→km/h (solo proveedor A).
- Cast de tipos: todos los campos numéricos de B llegan como texto desde el CSV.
- Normalización de fecha/hora a ISO 8601, incluyendo el supuesto de zona horaria para B (ver sección 5).
- Mapeo de `origin_code`/`source` al valor institucional fijo (`proveedor_a` / `proveedor_b`).
- Homogeneización de nombres de campo según la tabla anterior.

## 3. Tipos de errores encontrados antes de enviar información

Se adoptó un criterio explícito para distinguir dos categorías (implementado en `normalizacion.py` y `validacion.py`):

- **Error de normalización** (el dato no puede representarse en el tipo exigido): campo ausente (`A-0040` sin `observed_at`, `A-0150` sin `country_code`), valor no numérico (`temperature_f: "N/A"`, `temp_celsius: "error"`), valor nulo (`temperature_f: null`), texto vacío en un campo numérico/fecha (`measurement_time: ""`), o fecha con formato inválido (`"09-XX-2026 25:61"`, `"31/13/2026 28:75"`). En la ejecución real se encontraron **9** casos.
- **Rechazo por validación local** (el dato sí se representa correctamente pero incumple una regla de negocio del contrato): texto vacío en `ciudad`/`pais` (que sí es un string válido, solo que vacío), coordenadas fuera de rango (`latitud: 95.245`, `longitud: -190.75`), humedad fuera de 0–100 (`117.5`, `108.4`) y viento negativo (`-8.64`). En la ejecución real se encontraron **11** casos.

## 4. Diferencias entre validación local y validación del servidor

La validación local solo puede verificar las reglas explícitas del contrato (rangos, campos no vacíos, tipos). No puede anticipar reglas que dependan del estado del servidor, como duplicados (`409 Conflicto`) o reglas de negocio adicionales no documentadas que el servidor aplique internamente (`422`). Por eso el cliente igual interpreta la respuesta de la API para cada envío en vez de asumir que "validado localmente" equivale a "aceptado". En la ejecución real, la API devolvió un código no documentado explícitamente para el equipo de prueba (403, probablemente por falta de un identificador de equipo válido/autorizado), lo cual el cliente manejó sin caerse, clasificándolo como rechazo no reintentable.

## 5. Decisión de implementación más importante

La decisión más relevante fue separar explícitamente **error de normalización** de **rechazo de validación local**, en vez de tratarlos como una sola categoría de "registro descartado". Esto es importante porque el enunciado exige comportamientos distintos para cada uno (los rechazados localmente deben *permanecer* en `normalizadas.json`; los que fallan en normalización *no*), y porque en un escenario real esta distinción indica causas de falla muy diferentes: un error de normalización sugiere un problema estructural en la fuente (dato faltante o corrupto), mientras que un rechazo local indica un dato bien formado pero fuera de las reglas de negocio (posible error de sensor o de calibración). Un supuesto adicional documentado aquí: dado que el proveedor B no incluye zona horaria, se asumió que sus timestamps están en hora local de Colombia (`-05:00`), igual que el offset que ya trae el proveedor A, para mantener consistencia entre ambas fuentes.

## Evidencia resumida de una ejecución real

Ejecución local (`python integrador.py`) sobre los datasets suministrados:

| Métrica | Valor |
|---|---:|
| Registros procesados | 400 |
| Registros normalizados | 391 |
| Errores de normalización | 9 |
| Válidos localmente | 380 |
| Rechazados localmente | 11 |
| Enviados a la API | 380 |
| Aceptados por la API | 380 |
| Rechazados por la API | 0 |
| Errores de comunicación | 0 |


Ejemplo de error de normalización (id `A-0082`): `"No se pudo convertir: temperatura_c (measurements.temperature_f)"` porque el proveedor entregó `"N/A"`.

Ejemplo de rechazo local (id `A-0015`): `"humedad fuera de rango (0 a 100): 108.4"`.

Ejemplo de respuesta recibida desde la API (registro `A-0001`): código HTTP `403`, clasificado como `rechazado_api` sin reintento (por ser un código de la familia 4xx).

Resultado de la consulta final (`GET /api/v1/mediciones?equipo=...`): código HTTP `403` en este entorno de pruebas sin acceso de red; el detalle completo queda en el campo `consulta_final_api` de `salida/reporte.json`.

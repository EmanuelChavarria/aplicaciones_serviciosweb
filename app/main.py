from fastapi.responses import RedirectResponse
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import medicion, sensor, sensor_magnitud
from app.config import get_settings
from app.database.connection import verificar_conexion
from app.mqtt import client as mqtt_client

logger = logging.getLogger("app")


def configurar_logging() -> None:
    settings = get_settings()
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if settings.log_file:
        os.makedirs(os.path.dirname(settings.log_file) or ".", exist_ok=True)
        handlers.append(logging.FileHandler(settings.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=handlers,
        force=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configurar_logging()
    settings = get_settings()

    verificar_conexion()  # falla rápido si PostgreSQL no responde
    logger.info("Conexión a PostgreSQL verificada")

    cliente = None
    if settings.mqtt_enabled:
        logger.info("Sensor asignado: %s | Tópico: %s", settings.sensor_codigo, settings.mqtt_topic)
        cliente = mqtt_client.iniciar(settings)
    else:
        logger.warning("MQTT deshabilitado (MQTT_ENABLED=false): solo se sirve la API")

    yield

    if cliente is not None:
        mqtt_client.detener(cliente)
        logger.info("Cliente MQTT detenido")


app = FastAPI(
    title="API IoT — Taller 2",
    description="Adquisición por MQTT, validación y consulta de mediciones de sensores.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(sensor.router)
app.include_router(sensor_magnitud.router)
app.include_router(medicion.router)

"""Cliente MQTT (suscriptor).

Responsabilidad única: recibir mensajes del broker y delegarlos al servicio de
ingesta. Los errores se manejan aquí DENTRO (log + descarte); nunca se
convierten en HTTP porque MQTT no tiene cliente al que responder.
"""

import logging

import paho.mqtt.client as mqtt

from app.config import Settings, get_settings
from app.database.connection import get_session_factory
from app.services.ingesta import procesar_mensaje

logger = logging.getLogger(__name__)


def crear_cliente(settings: Settings | None = None) -> mqtt.Client:
    settings = settings or get_settings()
    if not settings.mqtt_broker:
        raise RuntimeError("Falta MQTT_BROKER. Configúralo en el archivo .env.")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password or "")

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            logger.error("Error de conexión MQTT: %s", reason_code)
            return
        logger.info("Conectado al broker %s:%s", settings.mqtt_broker, settings.mqtt_port)
        # Se suscribe aquí (y no en main) para re-suscribirse tras cada reconexión.
        result, _ = client.subscribe(settings.mqtt_topic)
        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.error("No fue posible suscribirse a %s (código %s)", settings.mqtt_topic, result)
        else:
            logger.info("Suscrito al tópico: %s", settings.mqtt_topic)

    def on_disconnect(client, userdata, flags, reason_code, properties=None):
        logger.warning("Desconectado del broker (%s); paho intentará reconectar", reason_code)

    def on_message(client, userdata, message):
        logger.info("Mensaje recibido en %s: %s", message.topic, message.payload.decode("utf-8", "replace"))
        # Una sesión nueva por mensaje: este callback corre en el hilo de paho.
        db = get_session_factory()()
        try:
            resultado = procesar_mensaje(db, message.payload, settings.sensor_codigo)
        except Exception:  # noqa: BLE001 - un mensaje malo jamás debe tumbar el hilo MQTT
            logger.exception("Error inesperado procesando el mensaje; se descarta")
            return
        finally:
            db.close()

        if resultado.aceptado:
            logger.info("ACEPTADO [%s] %s", resultado.codigo, resultado.detalle)
        else:
            logger.warning("RECHAZADO [%s] %s", resultado.codigo, resultado.detalle)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    return client


def iniciar(settings: Settings | None = None) -> mqtt.Client:
    """Conecta y arranca el bucle de red en un hilo de fondo (no bloquea FastAPI)."""
    settings = settings or get_settings()
    client = crear_cliente(settings)
    client.connect_async(settings.mqtt_broker, settings.mqtt_port, settings.mqtt_keepalive)
    client.loop_start()
    return client


def detener(client: mqtt.Client) -> None:
    client.loop_stop()
    client.disconnect()

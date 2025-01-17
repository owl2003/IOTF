import paho.mqtt.client as mqtt
import logging
from IOTF.backend.config import MQTT_BROKER,MQTT_PORT,CA_CERT_PATH
import ssl

logging.basicConfig(level=logging.INFO)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("MQTT connected successfully.")
    else:
        logging.error(f"MQTT connection failed with code {rc}.")




def start_mqtt(robot_id):

    client = mqtt.Client(client_id=robot_id,clean_session=True)

    client.tls_set(ca_certs=CA_CERT_PATH, certfile=None, keyfile=None, tls_version=ssl.PROTOCOL_TLS)

    client.will_set(
        topic=f"{robot_id}/status",
        payload="OFFLINE",
        qos=1,
        retain=True
    )
    client.on_connect = on_connect

    try:

        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        logging.info("MQTT client started successfully ")
        client.publish(f"{robot_id}/status", "CONNECTED", retain=True)
        return client
    except Exception as e:
        logging.error(f"Failed to start MQTT client: {e}")
        return None

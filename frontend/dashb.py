import sys
import ssl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLabel, QLineEdit, QComboBox
)
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import  pyqtSlot
import paho.mqtt.client as mqtt
from IOTF.backend.config import MQTT_BROKER, MQTT_PORT, CA_CERT_PATH


class MQTTDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MQTT Dashboard")
        self.setGeometry(100, 100, 800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.create_subscribe_section(layout)
        self.create_publish_section(layout)
        self.create_log_section(layout)
        self.init_mqtt()

    def create_subscribe_section(self, layout):
        subscribe_section = QWidget()
        subscribe_layout = QVBoxLayout(subscribe_section)
        self.subscribe_topic_input = QLineEdit()
        self.subscribe_topic_input.setPlaceholderText("Enter topic to subscribe")
        subscribe_layout.addWidget(self.subscribe_topic_input)
        subscribe_button = QPushButton("Subscribe")
        subscribe_button.clicked.connect(self.subscribe_to_topic)
        subscribe_layout.addWidget(subscribe_button)
        layout.addWidget(subscribe_section)

    def create_publish_section(self, layout):
        publish_section = QWidget()
        publish_layout = QVBoxLayout(publish_section)

        # Topic input
        self.publish_topic_input = QLineEdit()
        self.publish_topic_input.setPlaceholderText("Enter topic to publish")
        publish_layout.addWidget(self.publish_topic_input)

        self.publish_message_input = QLineEdit()
        self.publish_message_input.setPlaceholderText("Enter message")
        publish_layout.addWidget(self.publish_message_input)

        self.publish_qos_input = QComboBox()
        self.publish_qos_input.addItems(["0", "1", "2"])
        publish_layout.addWidget(QLabel("QoS"))
        publish_layout.addWidget(self.publish_qos_input)

        publish_button = QPushButton("Publish Message")
        publish_button.clicked.connect(self.publish_message)
        publish_layout.addWidget(publish_button)

        layout.addWidget(publish_section)

    def create_log_section(self, layout):
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("border: 1px solid #ccc; margin: 5px; padding: 5px;")
        layout.addWidget(self.log_display)

    def init_mqtt(self):
        self.mqtt_client = mqtt.Client(client_id="client_per", clean_session=True)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_log = self.on_log

        try:
            self.mqtt_client.tls_set(ca_certs=CA_CERT_PATH, certfile=None, keyfile=None, tls_version=ssl.PROTOCOL_TLS)
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.log_message(f"MQTT Error: {str(e)}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log_message("Connected to MQTT broker.")
        else:
            self.log_message(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        message = msg.payload.decode()
        # Use thread-safe method to update the GUI
        self.log_message_safe(f"Received on [{topic}]: {message}")

    @pyqtSlot(str)
    def log_message_safe(self, message):
        """Thread-safe method to log messages to the GUI."""
        self.log_display.append(message)
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)

    def on_disconnect(self, client, userdata, rc):
        self.log_message(f"Disconnected from MQTT broker. Return code: {rc}")

    def on_log(self, client, userdata, level, buf):
        pass

    def subscribe_to_topic(self):
        topic = self.subscribe_topic_input.text()
        if topic:
            self.mqtt_client.subscribe(topic)
            self.log_message(f"Subscribed to topic: {topic}")
        else:
            self.log_message("Error: Topic cannot be empty.")

    def publish_message(self):
        topic = self.publish_topic_input.text()
        message = self.publish_message_input.text()
        qos = int(self.publish_qos_input.currentText())

        if topic and message:
            try:
                self.mqtt_client.publish(topic, message, qos=qos)
                self.log_message(f"Published to [{topic}]: {message} (QoS: {qos})")
            except Exception as e:
                self.log_message(f"Publish Error: {str(e)}")
        else:
            self.log_message("Error: Topic and message cannot be empty.")

    def log_message(self, message):
        """Non-thread-safe method to log messages (for use in the main thread)."""
        self.log_display.append(message)
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = MQTTDashboard()
    dashboard.show()
    sys.exit(app.exec_())

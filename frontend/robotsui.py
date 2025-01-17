import sys
from PyQt5.QtWidgets import (QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QPlainTextEdit,QSpinBox,QTabWidget,)
from PyQt5.QtCore import pyqtSignal

from backend.robots._robots import RobotC, RobotA

class RobotControl(QWidget):
    message_received = pyqtSignal(str, str)  # Signal for thread-safe GUI updates

    def __init__(self, robot_type):
        super().__init__()
        self.robot_type = robot_type
        self.robot_id = None
        self.robot = None
        self.action_topic = None
        self.sensor_topic = None
        self.bomber_action_topic = None
        self.subscriptions = []

        self.setup_ui()
        self.message_received.connect(self.display_received_message)

        self.setWindowTitle(f"{robot_type} Configuration Panel")

    def setup_ui(self):
        main_layout = QVBoxLayout()


        id_layout = QHBoxLayout()
        self.id_label = QLabel("Robot ID:")
        self.id_line_edit = QLineEdit()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_robot)
        id_layout.addWidget(self.id_label)
        id_layout.addWidget(self.id_line_edit)
        id_layout.addWidget(self.start_button)
        main_layout.addLayout(id_layout)


        topic_layout = QHBoxLayout()
        self.initialize_button = QPushButton("Initialize Topics")
        self.initialize_button.clicked.connect(self.initialize_topics)
        topic_layout.addWidget(self.initialize_button)

        if self.robot_type == "RobotC":
            topic_layout.addWidget(QLabel("Bomber Action Topic:"))
            self.bomber_action_topic_edit = QLineEdit()
            topic_layout.addWidget(self.bomber_action_topic_edit)

        topic_layout.addWidget(QLabel("Action Topic:"))
        self.action_topic_edit = QLineEdit()
        topic_layout.addWidget(self.action_topic_edit)

        topic_layout.addWidget(QLabel("Sensor Topic:"))
        self.sensor_topic_edit = QLineEdit()
        topic_layout.addWidget(self.sensor_topic_edit)
        main_layout.addLayout(topic_layout)

        if self.robot_type == "RobotA":
            sensor_layout = QHBoxLayout()
            self.start_sensor_button = QPushButton("Start Scenario")
            self.stop_sensor_button = QPushButton("Stop Sensor")
            self.start_sensor_button.clicked.connect(self.start_sensor)
            self.stop_sensor_button.clicked.connect(self.stop_sensor)
            sensor_layout.addWidget(self.start_sensor_button)
            sensor_layout.addWidget(self.stop_sensor_button)
            main_layout.addLayout(sensor_layout)


        subscription_layout = QHBoxLayout()
        self.subscription_topic_edit = QLineEdit()
        self.subscription_topic_edit.setPlaceholderText("Enter topic to subscribe")
        self.add_subscription_button = QPushButton("Add Subscription")
        self.add_subscription_button.clicked.connect(self.subscribe_to)
        subscription_layout.addWidget(self.subscription_topic_edit)
        subscription_layout.addWidget(self.add_subscription_button)
        main_layout.addLayout(subscription_layout)


        publish_layout = QHBoxLayout()
        self.publish_topic_edit = QLineEdit()
        self.publish_topic_edit.setPlaceholderText("Publish topic")
        self.publish_message_edit = QLineEdit()
        self.publish_message_edit.setPlaceholderText("Message")
        self.qos_spinbox = QSpinBox()
        self.qos_spinbox.setRange(0, 2)
        self.qos_spinbox.setPrefix("QoS: ")
        self.publish_button = QPushButton("Publish")
        self.publish_button.clicked.connect(self.publish_message)

        publish_layout.addWidget(self.publish_topic_edit)
        publish_layout.addWidget(self.publish_message_edit)
        publish_layout.addWidget(self.qos_spinbox)
        publish_layout.addWidget(self.publish_button)
        main_layout.addLayout(publish_layout)


        self.subscriptions_text = QPlainTextEdit()
        self.subscriptions_text.setReadOnly(True)
        self.subscriptions_text.setMaximumHeight(100)
        main_layout.addWidget(QLabel("Active Subscriptions:"))
        main_layout.addWidget(self.subscriptions_text)


        self.tabs = QTabWidget()


        self.messages_log = QPlainTextEdit()
        self.messages_log.setReadOnly(True)
        self.messages_tab = QWidget()
        messages_layout = QVBoxLayout()
        messages_layout.addWidget(self.messages_log)
        self.messages_tab.setLayout(messages_layout)


        self.system_log = QPlainTextEdit()
        self.system_log.setReadOnly(True)
        self.system_tab = QWidget()
        system_layout = QVBoxLayout()
        system_layout.addWidget(self.system_log)
        self.system_tab.setLayout(system_layout)

        self.tabs.addTab(self.messages_tab, "Received Messages")
        self.tabs.addTab(self.system_tab, "System Log")
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)

    def start_robot(self):
        self.robot_id = self.id_line_edit.text()
        if not self.robot_id:
            self.update_log("Error: Please enter a Robot ID")
            return

        if self.robot_type == "RobotC":
            self.robot = RobotC(self.robot_id, self.message_received.emit)
        elif self.robot_type == "RobotA":
            self.robot = RobotA(self.robot_id, self.message_received.emit)

        self.update_log(f"Started {self.robot_type} with ID: {self.robot_id}")

    def initialize_topics(self):
        if not self.robot:
            self.update_log("Error: Please start the robot first")
            return

        self.action_topic = self.action_topic_edit.text()
        self.sensor_topic = self.sensor_topic_edit.text()

        if self.robot_type == "RobotC":
            self.bomber_action_topic = self.bomber_action_topic_edit.text()
            self.robot.initialize_topics(
                self.action_topic, self.sensor_topic, self.bomber_action_topic
            )
        else:
            self.robot.initialize_topics(self.action_topic, self.sensor_topic)

        self.update_log("Topics initialized")

    def start_sensor(self):
        if not self.robot:
            self.update_log("start the robot first")
            return

        self.robot.start_sensor()
        self.update_log("sensor started")

    def stop_sensor(self):
        if not self.robot:
            self.update_log("start the robot first")
            return

        self.robot.stop_sensor()
        self.update_log("sensor stopped")

    def subscribe_to(self):
        if not self.robot:
            self.update_log("start the robot first")
            return

        topic = self.subscription_topic_edit.text()
        if topic:
            self.robot.subscribe_to(topic)
            self.subscriptions.append(topic)
            self.update_subscriptions_display()
            self.subscription_topic_edit.clear()
            self.update_log(f"Subscribed to: {topic}")

    def update_subscriptions_display(self):
        self.subscriptions_text.setPlainText("\n".join(self.subscriptions))

    def publish_message(self):
        if not self.robot:
            self.update_log("Please start the robot first")
            return

        topic = self.publish_topic_edit.text()
        message = self.publish_message_edit.text()
        qos = self.qos_spinbox.value()

        if not topic or not message:
            self.update_log("Please enter both topic and message")
            return

        self.robot.publish(topic, message, qos)
        self.update_log(f"Published to {topic} with QoS {qos}: {message}")

    def display_received_message(self, topic, payload):
        message = f"Topic: {topic}Message: {payload}\n"
        self.messages_log.appendPlainText(message)

    def update_log(self, message):

        self.system_log.appendPlainText(f"{message}")


    def closeEvent(self, event):

        if self.robot:
            self.robot.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    robot_R1_window = RobotControl("RobotC")
    robot_R2_window = RobotControl("RobotC")
    robot_a_window = RobotControl("RobotA")

    robot_R1_window.setGeometry(100, 100, 800, 600)
    robot_R2_window.setGeometry(800, 300, 800, 600)
    robot_a_window.setGeometry(900, 100, 800, 600)

    robot_R1_window.show()
    robot_R2_window.show()
    robot_a_window.show()

    sys.exit(app.exec_())
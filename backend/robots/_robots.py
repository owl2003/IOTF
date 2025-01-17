import threading
import time
import random
from backend.mqtt_client import start_mqtt


class RobotC:
    def __init__(self, robot_id, message_callback=None):


        self.bomber_action_topic = None
        self.sensor_topic = None
        self.action_topic = None
        self.client = start_mqtt(f"rifle{robot_id}")
        self.robot_id = robot_id
        self.message_callback = message_callback
        self.sensor_running = False
        self.dead = False
        self.damage_level = 0

    def initialize_topics(self, action_topic, sensor_topic, bomber_action_topic):

        self.action_topic = action_topic
        self.sensor_topic = sensor_topic
        self.bomber_action_topic = bomber_action_topic
        if bomber_action_topic:
         self.subscribe_to(bomber_action_topic)


    def subscribe_to(self,topic):
        self.client.subscribe(topic)
        self.client.on_message = self.on_message

    def publish(self, topic, message, qos):
        self.client.publish(topic, message, qos)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        message = msg.payload.decode()
        if self.message_callback:
            self.message_callback(topic, message)

        try:
            if topic == self.action_topic:
                self.handle_action(message)
            elif topic == self.bomber_action_topic:
                self.handle_bomber_action(message)
            else:
                print(f"Unhandled topic: {topic}")
        except Exception as e:
            print(f"Error processing message: {e}")
        return topic, message

    def handle_bomber_action(self, message):


        if self.dead:
            return
        if message == "COOLING_DOWN":
            self.start_sensor()
            self.client.publish(self.action_topic, "SHOOT")
        elif message == "BOMB_DROP":
            self.stop_sensor()
            self.client.publish(self.action_topic, "DODGE")
            self.client.publish(self.sensor_topic, self.damage_level, retain=True)

    def handle_death(self):
        self.client.publish(self.action_topic, "WHAT2DO", retain=True)


    def handle_action(self, message):

        if not self.dead:
            return

        if message == "EXPLODE":
            self.client.publish(self.action_topic, "EXECUTED",retain=True)
            self.client.publish(f"rifle{self.robot_id}/status", "OFFLINE", retain=True)
            self.client.publish(self.damage_level, "*****", retain=True)

            self.client.disconnect()
            self.stop_sensor()
        elif message == "BACK2BASE":
            self.damage_level = 0
            self.dead = False

    def start_sensor(self):

        if not self.sensor_running:
            self.sensor_running = True
            threading.Thread(target=self.simulate_rifle_sensor, daemon=True).start()

    def stop_sensor(self):


        self.sensor_running = False

    def simulate_rifle_sensor(self):


        while self.sensor_running:
            self.damage_level += random.randint(7, 20)
            self.client.publish(self.sensor_topic, f"{self.damage_level}", retain=True)
            if self.damage_level >= 100:
                self.dead = True
                self.stop_sensor()
                self.handle_death()
                break
            time.sleep(4)


class RobotA:
    def __init__(self, robot_id, message_callback=None):


        self.sensor_running = False
        self.subscriptions = None
        self.sensor_topic = None
        self.action_topic = None
        self.client = start_mqtt(f"bomber{robot_id}")
        self.message_callback = message_callback
        self.robot_id = robot_id



    def initialize_topics(self, action_topic, sensor_topic):


        self.action_topic = action_topic
        self.sensor_topic = sensor_topic

    def on_message(self, client, userdata, msg):

        topic = msg.topic
        message = msg.payload.decode()

        if self.message_callback:
            self.message_callback(topic, message)
        print(f"Received message on topic {topic}: {message}")

    def subscribe_to(self,topic):
        self.client.subscribe(topic)
        self.client.on_message = self.on_message

    def publish(self, topic, message,qos=1):
        self.client.publish(topic, message,qos)

    def stop_sensor(self):

        self.sensor_running = False

    def start_sensor(self):


        if not self.sensor_running:
            self.sensor_running = True
            threading.Thread(target=self.simulate_bomber_sensor, daemon=True).start()

    def simulate_bomber_sensor(self):
        temperature = 100
        while self.sensor_running:
            temperature += 20
            if self.client:
                self.client.publish(self.sensor_topic, f"{temperature}",retain=True)
                self.client.publish(self.action_topic, "BOMB_DROP", retain=True)
                time.sleep(2)
                if temperature >= 300:
                    while temperature > 100:
                         self.client.publish(self.sensor_topic, f"{temperature}",retain=True)
                         self.client.publish(self.action_topic, "COOLING_DOWN",retain=True)
                         temperature -= 30
                         time.sleep(2)
        time.sleep(2)





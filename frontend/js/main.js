let mqttClient;

const robotTopics = {
  'bomber3': {
    sensor: '',
    action: '',
    status: ''
  },
  'rifle1': {
    sensor: '',
    action: '',
    status: ''
  },
  'rifle2': {
    sensor: '',
    action: '',
    status: ''
  }
};

const robotUI = {
  'bomber3': {
    sensorDisplay: 'temperature-bomber',
    actionDisplay: 'action-bomber',
    statusDisplay: 'status-bomber3'
  },
  'rifle1': {
    sensorDisplay: 'damage-rifle1',
    actionDisplay: 'action-rifle1',
    statusDisplay: 'status-rifle1'
  },
  'rifle2': {
    sensorDisplay: 'damage-rifle2',
    actionDisplay: 'action-rifle2',
    statusDisplay: 'status-rifle2'
  }
};

function connectToMqtt(username, password, id) {
  mqttClient = mqtt.connect('wss://localhost:9001', {
    username: username,
    password: password,
    rejectUnauthorized: true,
    clientId: id,
    clean: true,
    reconnectPeriod: 5,
  });

  mqttClient.on('connect', () => {
    console.log('Connected to MQTT broker');
    document.getElementById('robot-container').style.display = 'block';
    document.getElementById('login-form').style.display = 'none';
  });

  mqttClient.on('message', (topic, message) => {
    logMessage(`Received message on ${topic}: ${message.toString()}`);
    handleMqttMessage(topic, message.toString());
  });

  mqttClient.on('error', (error) => {
    console.error('MQTT Error:', error);
    alert('Failed to connect to MQTT broker. Check your credentials.');
  });

  setupEventListeners();
}

function setupEventListeners() {
  const saveButtons = document.querySelectorAll('button[data-robot][data-topic-type]');

  saveButtons.forEach(button => {
    button.addEventListener('click', function() {
      const robot = this.getAttribute('data-robot');
      const topicType = this.getAttribute('data-topic-type');
      const inputId = `${topicType}-topic-${robot}`;
      const topic = document.getElementById(inputId).value;

      if (!topic) {
        alert('Topic cannot be empty.');
        return;
      }

      if (robotTopics[robot][topicType]) {
        mqttClient.unsubscribe(robotTopics[robot][topicType]);
      }

      robotTopics[robot][topicType] = topic;
      mqttClient.subscribe(topic, { qos: 0 });
      logMessage(`Subscribed to ${topicType} topic for ${robot}: ${topic}`);
    });
  });

  document.getElementById('send-message').addEventListener('click', function() {
    const topic = document.getElementById('topic').value;
    const message = document.getElementById('message').value;
    const qos = parseInt(document.getElementById('qos').value);
    mqttClient.publish(topic, message, { qos: qos });
    logMessage(`Sent message to ${topic}: ${message} with QoS ${qos}`);
  });

  document.getElementById('subscribe-topic').addEventListener('click', function() {
    const topic = document.getElementById('subscribe').value;
    mqttClient.subscribe(topic, { qos: 0 });
    logMessage(`Subscribed to topic: ${topic}`);
  });
}

    function handleMqttMessage(topic, message) {
      for (const robot in robotTopics) {
        const topics = robotTopics[robot];
      if (topic === topics.sensor) {
      const ui = robotUI[robot];
        document.getElementById(ui.sensorDisplay).textContent = `Sensor: ${message}`;
        const sensorValue = parseInt(message);
        let color;
        if (sensorValue >= 300) {
        color = 'red';
      } else if (sensorValue > 160) {
        color = 'orange';
      } else {
        color = 'blue';
      }
      document.getElementById(ui.sensorDisplay).style.color = color;
    } else if (topic === topics.action) {
       const ui = robotUI[robot];
        document.getElementById(ui.actionDisplay).textContent = `Action: ${message}`;
      let color;
      if (message === 'COOLING_DOWN') {
        color = 'blue';
        } else if (message === 'BOMB_DROP') {
        color = 'red';
      } else {
          color = 'green';
      }
      document.getElementById(ui.actionDisplay).style.color = color;
     } else if (topic === topics.status) {
        const ui = robotUI[robot];
      document.getElementById(ui.statusDisplay).textContent = `Status: ${message}`;
       let color;
        if (message === 'OFFLINE') {
        color = 'red';
          } else if (message === 'CONNECTED') {
        color = 'green';
      } else {
          color = 'gray';
      }
        document.getElementById(ui.statusDisplay).style.color = color;
    }
  }
}

              function logMessage(message) {
                const logArea = document.getElementById('log-area');
                logArea.value += message + '\n';
                 logArea.scrollTop = logArea.scrollHeight;
            }

document.getElementById('login').addEventListener('submit', function(event) {
    event.preventDefault();
   const username = document.getElementById('username').value;
     const password = document.getElementById('password').value;
  const id = document.getElementById('id').value;

  connectToMqtt(username, password, id);
});
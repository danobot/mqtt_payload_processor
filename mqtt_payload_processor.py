# MQTT Payload Processor for Home Assistant
# Converts MQTT message payloads to Home Assistant events and callback functions.
#
# Documentation:    https://github.com/danobot/mqtt_payload_processor
# Version:          v0.2.3

import homeassistant.loader as loader
import logging
import datetime

VERSION = '0.2.3'

DOMAIN = 'mqtt_payload_processor'

DEPENDENCIES = ['mqtt']

CONF_TOPIC = 'topic'
DEFAULT_TOPIC = '/rf/'

_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    CONFIG = config[DOMAIN]

    # _LOGGER.info(CONFIG)
    """Set up the Hello MQTT component."""
    #mqtt = loader.get_component('mqtt')
    mqtt = hass.components.mqtt
    topic = CONFIG.get('topic', DEFAULT_TOPIC)
    globalCallbackScript = CONFIG.get('callback_script', None)
    entities = []


    for v in CONFIG['entities']:
        m = MqttPayloadProcessor(v)
        entities.append(m)

    

    for v in entities:
        v.setState(v, "None", True)



    def message_received(topic, payload, qos):
        """Handle new MQTT messages."""
        #hass.states.set('rf_processor.last_payload_received', payload)


        # find name of button from config

        for v in entities:
            v.processPayload(payload)

    # Subscribe our listener to a topic.
    mqtt.subscribe(topic, message_received)

    



    # Service to publish a message on MQTT.
    def set_state_service(call):
        """Service to send a message."""
        mqtt.publish(topic, call.data.get('new_state'))

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'set_state', set_state_service)

    # Return boolean to indicate that initialization was successfully.
    return True

class MqttPayloadProcessor():

    type = None
    payloads_on = []
    name = None
    def initialize(self, config):
        if config.get('payload'):
            self.payloads_on.append(config.get('payload'))
        if config.get('payloads'):
            self.payloads_on.extend(config.get('payloads'))
        self.name = config.get('name', "Unnamed")
        self.type = config.get('type', None)
        self.callback = config.get('callback', False)
        self.callback_script = config.get('callback_script', False)

    @property
    def device_state_attributes(self):
        return {}

    def processPayload(self, payload):
        
        # # single payload defined
        # if 'payload' in v:
        #     if int(v['payload']) == int(payload): 
        #         handleRFCode(v, payload);
        #         break;

        #  # multiple payloads defined
        for p in self.payloads_on:
            _LOGGER.info(p)
            if int(p) == int(payload):
                self.handleRFCode()
                self.setState(payload)

                break


    def handleRFCode(self):
        hass.states.set(DOMAIN + '.last_triggered_by', self.name)
        _LOGGER.info(self.name)
        # hass.states.set('rf_processor.last_triggered_time', time.localtime(time.time()))
        if CONFIG['event']:
            hass.bus.fire(self.name, {
                'state': 'on'
            })  

        log_data = {
            'name': self.name,        
            'message': 'was triggered'
        }
        if self.type == 'button':
            log_data['message'] = 'was pressed'

        if self.type == 'motion':
            log_data['message'] = 'was activated'

        hass.services.call('logbook', 'log', log_data)
        
        if globalCallbackScript is not None and self.callback:
            _LOGGER.info("Running global callback script: " + globalCallbackScript);
            hass.services.call('script', 'turn_on', {'entity_id': globalCallbackScript})
        
        if self.callback_script:
            device, script = self.callback_script.split('.')
            _LOGGER.info("Running device callback script: " + script)
            hass.services.call('script', 'turn_on', {'entity_id': self.callback_script})



        
    def setState(self, payload, init=False):
        if init:
            time = "Never"
        else:
            time = str(datetime.datetime.now())

        state = {
            'last_triggered': time, 
            'payload': payload
        }

        if self.type:
            state['type'] = self.type

        if self.callback_script:
            state['callback_script'] = self.callback_script

        if self.callback:
            state['callback'] = self.callback

        if globalCallbackScript is not None and 'callback' in v and v['callback']:
            state['global_callback'] = globalCallbackScript;

        entity = "{}.{}".format(DOMAIN, device['name'].replace('-','_'))
        hass.states.set(entity, state);
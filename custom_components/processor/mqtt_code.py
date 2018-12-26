# MQTT Payload Processor for Home Assistant
# Converts MQTT message payloads to Home Assistant events and callback scripts.
# Useful for storing implementation specific codes in one location and using 
# HA specific abstractions throughout the configuration.
# E.g. RF codes, Bluetooth ids, etc.

# Documentation:    https://github.com/danobot/mqtt_payload_processor
# Version:          v0.3.0

import homeassistant.loader as loader
import logging
import datetime
from homeassistant.helpers.entity import Entity
from custom_components.processor import ProcessorDevice

VERSION = '0.3.0'

DEPENDENCIES = ['mqtt']

CONF_TOPIC = 'topic'
DEFAULT_TOPIC = '/rf/'

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    
    entities = []

    mqtt = loader.get_component(hass, 'mqtt')
    topic = config.get('topic', DEFAULT_TOPIC)
    _LOGGER.info("Platform Config:" + str(config))

    for v in config['entities']:
        _LOGGER.info("Entity: " + str(v))
        v['globalCallbackScript'] = config.get('callback_script', None)
        m = None
        m = MqttPayloadProcessor(v)

        # must be done here because self.hass inside `m` is None for some reason
        # (even though it inherits from `Entity`)
        mqtt.subscribe(hass, topic, m.message_received)
        
        entities.append(m)

    
    add_entities(entities)

    return True

class MqttPayloadProcessor(ProcessorDevice):

    type = None
    payloads_on = []
    name = None
    last_payload = None
    def __init__(self, config):
        ProcessorDevice.__init__(self,config)
        self.payloads_on = []
    
        self.name = config.get('name', "Unnamed")
        self._unique_id = self.name
        self.log = logging.getLogger(__name__ + '.' + self.name)
        self.log.info("Init Config: "  +str(config))
        self.log.info("Payloads: "  +str(self.payloads_on))
        if config.get('payload'):
            self.payloads_on.append(config.get('payload'))
        if config.get('payloads'):
            self.payloads_on.extend(config.get('payloads'))

        self.log.info(self.payloads_on)
        self.type = config.get('type', None)
        self.log_events = config.get('log', False)
        self.event = config.get('event', False)
        self.callback = config.get('callback', False)
        self.callback_script = config.get('callback_script', False)
        self.globalCallbackScript = config.get('globalCallbackScript', False)
        # _LOGGER.info(str(dir(self)))
        # _LOGGER.info(str(dir(self.hass)))
        
    @property
    def device_state_attributes(self):
        return {'payloads_on': self.payloads_on}

    def message_received(self, topic, payload, qos):
        """Handle new MQTT messages."""
        #hass.states.set('rf_processor.last_payload_received', payload)

        self.log.info("Message received: " + str(payload))
        # find name of button from config

        self.process(payload)

    def process(self, payload):
        
        self.log.info("Called process on {}".format(self.name))
        # # single payload defined
        # if 'payload' in v:
        #     if int(v['payload']) == int(payload): 
        #         handleRFCode(v, payload);
        #         break;

        #  # multiple payloads defined
        self.log.debug("Is {} a match in {}?".format(payload, str(self.payloads_on)))
        for p in self.payloads_on:
            if int(p) == int(payload):
                self.log.debug("Processing {} code".format(p))
                self.handleRFCode()
                # self.setState(payload)
                self.last_payload = payload
                self.async_schedule_update_ha_state(True)

                break



    def handleRFCode(self):
        # self.hass.states.set(DOMAIN + '.last_triggered_by', self.name)
        self.log.info(self.name)
        # hass.states.set('rf_processor.last_triggered_time', time.localtime(time.time()))
        if self.event:
            self.hass.bus.fire(self.name, {
                'state': 'on'
            })  

        if self.log_events:
            log_data = {
                'name': self.name,        
                'message': 'was triggered'
            }
            if self.type == 'button':
                log_data['message'] = 'was pressed'

            if self.type == 'motion':
                log_data['message'] = 'was activated'

            self.hass.services.call('logbook', 'log', log_data)
        
        if self.globalCallbackScript is not None and self.callback:
            self.log.info("Running global callback script: " + self.globalCallbackScript)
            self.hass.services.call('script', 'turn_on', {'entity_id': self.globalCallbackScript})
        
        if self.callback_script:
            device, script = self.callback_script.split('.')
            self.log.info("Running device callback script: " + script)
            self.hass.services.call('script', 'turn_on', {'entity_id': self.callback_script})

    @property
    def state(self):
        """Return the state of the entity."""
        return None

    @property
    def state_attributes(self):
        """Return the state of the entity."""

        time = str(datetime.datetime.now())

        state = {
            'last_triggered': time, 
            'payload': self.last_payload
        }

        if self.type:
            state['type'] = self.type

        if self.callback_script:
            state['callback_script'] = self.callback_script

        if self.callback:
            state['callback'] = self.callback

        if self.globalCallbackScript is not None:
            state['global_callback'] = self.globalCallbackScript

        return state


    
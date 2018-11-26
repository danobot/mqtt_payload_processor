# MQTT Payload Processor for Home Assistant
# Converts MQTT message payloads to Home Assistant events and callback functions.
#
# Documentation:    https://github.com/danobot/mqtt_payload_processor
# Version:          v0.2.1

import homeassistant.loader as loader
import logging
import datetime

DOMAIN = 'mqtt_payload_processor'

DEPENDENCIES = ['mqtt']

CONF_TOPIC = 'topic'
DEFAULT_TOPIC = '/rf/'

def setup(hass, config):
    CONFIG = config[DOMAIN]
    _LOGGER = logging.getLogger(__name__)

    # _LOGGER.info(CONFIG)
    """Set up the Hello MQTT component."""
    #mqtt = loader.get_component('mqtt')
    mqtt = hass.components.mqtt
    topic = CONFIG.get('topic', DEFAULT_TOPIC)
    globalCallbackScript = CONFIG.get('callback_script', None)

    def setState(device, payload, init=False):
        if init:
            time = "Never"
        else:
            time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%z") # 2018-11-26T10:50:27.636933+00:00

        state = {
            'last_triggered': time, 
            'payload': payload
        };

        if 'type' in device:
            state['type'] = device['type'];

        if 'callback_script' in device:
            state['callback_script'] = device['callback_script'];

        if 'callback' in device:
            state['callback'] = device['callback'];

        if globalCallbackScript is not None and 'callback' in v and v['callback']:
            state['global_callback'] = globalCallbackScript;

        entity = "{}.{}".format(DOMAIN, device['name'].replace('-','_'));
        hass.states.set(entity, state);

    for v in CONFIG['entities']:
        setState(v, "None", True);



    def message_received(topic, payload, qos):
        """Handle new MQTT messages."""
        #hass.states.set('rf_processor.last_payload_received', payload)


        # find name of button from config

        for v in CONFIG['entities']:

            # single payload defined
            if 'payload' in v:
                if int(v['payload']) == int(payload): 
                    handleRFCode(v, payload);
                    break;

            #  # multiple payloads defined
            if 'payloads' in v:
                for p in v['payloads']:
                    _LOGGER.info(p);
                    if int(p) == int(payload):
                        handleRFCode(v, payload);
                        break;


    # Subscribe our listener to a topic.
    mqtt.subscribe(topic, message_received)

    def handleRFCode(v, payload):
        hass.states.set(DOMAIN + '.last_triggered_by', v['name'])
        _LOGGER.info(v['name'])
        # hass.states.set('rf_processor.last_triggered_time', time.localtime(time.time()))
        if CONFIG['event']:
            hass.bus.fire(v['name'], {
                'state': 'on'
            })

        log_data = {
            'name': v['name'],        
            'message': 'was triggered'
        };
        if 'type' in v:
            if v['type'] == 'button':
                log_data['message'] = 'was pressed';

            if v['type'] == 'motion':
                log_data['message'] = 'was activated';

        hass.services.call('logbook', 'log', log_data);
        
        if globalCallbackScript is not None and 'callback' in v and v['callback']:
            _LOGGER.info("Running global callback script: " + globalCallbackScript);
            hass.services.call('script', 'turn_on', {'entity_id': globalCallbackScript});
        
        if 'callback_script' in v:
            device, script = v['callback_script'].split('.');
            _LOGGER.info("Running device callback script: " + script);
            hass.services.call('script', 'turn_on', {'entity_id': v['callback_script']});

        setState(v, payload)



    # Service to publish a message on MQTT.
    def set_state_service(call):
        """Service to send a message."""
        mqtt.publish(topic, call.data.get('new_state'))

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'set_state', set_state_service)

    # Return boolean to indicate that initialization was successfully.
    return True

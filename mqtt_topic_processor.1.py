import homeassistant.loader as loader
import logging
import time
# The domain of your component. Should be equal to the name of your component.
DOMAIN = 'rf_processor'

# List of component names (string) your component depends upon.
DEPENDENCIES = ['mqtt']


CONF_TOPIC = 'topic'
DEFAULT_TOPIC = '/rf/'
DEFAULT_TIMEOUT = 5
# event:    Global overwrite, generates events based on rf code name when set to true
# reset:    Sends off event after some timeout
# timeout:  overwrite default timeout
def setup(hass, config):
    CONFIG = config[DOMAIN]
    _LOGGER = logging.getLogger(__name__)

    # _LOGGER.info(CONFIG)
    """Set up the Hello MQTT component."""
    #mqtt = loader.get_component('mqtt')
    mqtt = hass.components.mqtt
    topic = CONFIG.get('topic', DEFAULT_TOPIC)
    callback_script = CONFIG.get('callback_script', DEFAULT_TOPIC)
    entity_id = 'rf_processor.last_message'
    #hass.states.set('rf_processor.config', CONFIG)
    # Listener to be called when we receive a message.

    # for v in CONFIG['entities']:
    #     c = str(v['name']).replace('-','_');
    #     domain = ''
    #     state = {};
    #     if 'type' in v and v['type'] == 'button':
    #         domain = 'mqtt_button';
    #         state = {'name': v['name']}
    #         state['last_trigger'] = 'never';
    #     hass.states.set(domain + '.' + c, state)

    def message_received(topic, payload, qos):
        """Handle new MQTT messages."""
        #hass.states.set(entity_id, topic+" " + payload)
        #hass.states.set('rf_processor.last_payload_received', payload)


        # find name of button from config

        for v in CONFIG['entities']:

            if int(v['payload']) == int(payload): # single payload
                handleRFCode(v);
                break;

            if 'payloads' in v:
                for payload in v['payloads']: # multiple payloads defined
                    if int(payload) == int(payload):
                        handleRFCode(payload);
                        break;


    # Subscribe our listener to a topic.
    mqtt.subscribe(topic, message_received)

    # Set the initial state.
    hass.states.set(entity_id, 'No messages')
    def handleRFCode(v):
        hass.states.set('rf_processor.last_triggered_by', v['name'])
        # hass.states.set('rf_processor.last_triggered_time', time.localtime(time.time()))
        if CONFIG['event']:
            hass.bus.fire(v['name']+'-on', {
                'state': 'on'
            })
            hass.bus.fire(v['name'], {
                'state': 'on'
            })
        if 'type' in v and v['type'] == 'button':
            log_data = {'name': v['name'], 
            
            'message': 'was pressed'};
            hass.services.call('logbook', 'log',log_data);
        if 'beep' in v and v['beep']:
                hass.services.call('script', 'buzz_short')
                
        
        # entity = DOMAIN + '.'+str(v['name'])
        # _LOGGER.info(entity)
        # hass.states.set(entity, 'on')
        # 
        # hass.states.set(str(DOMAIN + '.'+v['name']), 'off')
        if CONFIG['event'] or v['event']:
            hass.bus.fire(v['name']+'-off', {
            'state': 'off'
            })

            hass.bus.fire('button', {
                'name': v['name']
            })

        # This is implementation specific. RF codes that require a reset command are handled here.
        # The MQTT message resets motion sensors to OFF.
        # This avoids having to define automations for each motion sensor.

        # if 'reset' in v and v['reset']:
        #         time.sleep(DEFAULT_TIMEOUT)
        #         payload = {
        #             "topic": "/rf/all",
        #             "payload": 0
        #         } 
        #         hass.services.call('mqtt', 'publish', payload,False)
    # Service to publish a message on MQTT.
    def set_state_service(call):
        """Service to send a message."""
        mqtt.publish(topic, call.data.get('new_state'))

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'set_state', set_state_service)

    # Return boolean to indicate that initialization was successfully.
    return True

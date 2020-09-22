"""
    Generic component for generic platforms that do stuff.

"""
DOMAIN = 'processor'
from homeassistant.helpers import discovery
import logging
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity import Entity
# from homeassistant.compoennts.alert import Alert
_LOGGER = logging.getLogger(__name__)
VERSION = '2.0.3'

DEPENDENCIES = ['mqtt']



async def async_setup(hass, config):
    """Set up the counters."""
    _LOGGER.info("settings uip")
    component = hass.data[DOMAIN] = EntityComponent(
        _LOGGER, DOMAIN, hass)

    await component.async_setup(config)
    # entities = []
    # CONFIG = config


    # mqtt = hass.components.mqtt
    # topic = CONFIG.get('topic', DEFAULT_TOPIC)
    # globalCallbackScript = CONFIG.get('callback_script', None)
    # entities = []
    # for object_id, cfg in config[DOMAIN].items():
    #     if not cfg:
    #         cfg = {}
    #     _LOGGER.info(cfg)
    #     v['globalCallbackScript'] = globalCallbackScript
    #     m = Processor(v)
    #     entities.append(m)

    # if not entities:
    #     return False

    # # component.async_register_entity_service(
    # #     SERVICE_INCREMENT, SERVICE_SCHEMA,
    # #     'async_increment')
    # # component.async_register_entity_service(
    # #     SERVICE_DECREMENT, SERVICE_SCHEMA,
    # #     'async_decrement')
    # # component.async_register_entity_service(
    # #     SERVICE_RESET, SERVICE_SCHEMA,
    # #     'async_reset')

    # await component.async_add_entities(entities)
    

    # def message_received(topic, payload, qos):
    #     """Handle new MQTT messages."""
    #     #hass.states.set('rf_processor.last_payload_received', payload)

    #     _LOGGER.info("Message received" + str(payload))
    #     # find name of button from config

    #     for v in entities:
    #         v.processPayload(payload)

    # # Subscribe our listener to a topic.
    # mqtt.subscribe(topic, message_received)

    return True

async def async_setup_entry(hass, entry):
    """Set up a config entry."""
    return await hass.data[DOMAIN].async_setup_entry(entry)


class ProcessorDevice(Entity):
    hass = None
  
    def __init__(self, config):
        self.hass = self.hass
        self.name = config.get('name', "Unnamed")
        self._unique_id = self.name
        self.log = logging.getLogger(__name__ + '.' + self.name)
        self.log.info(self.hass)

    @property
    def device_state_attributes(self):
        return {}

    def process(self, **kwargs):
        
        return None


    
    @property
    def state(self):
        """Return the state of the entity."""
        return None

    @property
    def state_attributes(self):
        """Return the state of the entity."""

        return None


        

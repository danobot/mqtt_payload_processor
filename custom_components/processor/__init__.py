"""
    Generic component for generic platforms that do stuff.

"""
DOMAIN = 'processor'
from homeassistant.helpers import discovery
import logging
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
import asyncio
# from homeassistant.compoennts.alert import Alert
_LOGGER = logging.getLogger(__name__)
VERSION = '2.1.0'

DEPENDENCIES = ['mqtt']
PLATFORMS = ['mqtt_code']






async def async_setup(hass, config):
    """Set up the Hello World component."""
    component = hass.data[DOMAIN] = EntityComponent(
        _LOGGER, DOMAIN, hass)
    _LOGGER.info("processor/__init__.py - async_setup")
    domain_config = config[DOMAIN]
    _LOGGER.info(" domain_config " + str(domain_config))


    hass.data.setdefault(DOMAIN, {})
    # load platforms
    _LOGGER.info(" loading platforms")

    for platform in PLATFORMS:
        # hass.async_create_task(
        hass.helpers.discovery.load_platform(platform, DOMAIN, domain_config, config)
        # )
    _LOGGER.info("after loading platforms")
    # await component.async_setup(config)

    return True






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




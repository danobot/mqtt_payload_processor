"""
    Generic processor component.
"""
import logging
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity import Entity
from importlib import import_module

_LOGGER = logging.getLogger(__name__)
VERSION = '3.1.2'

DEPENDENCIES = ['mqtt']
DOMAIN = "processor"
PLATFORMS = ["mqtt_code"]

async def async_setup(hass, config):
    """Set up the Processor component."""
    _LOGGER.info("PROCESSOR INIT - async_setup")
    domain_config = config.get(DOMAIN, [])

    # EntityComponent handles adding entities to Home Assistant
    component = hass.data[DOMAIN] = EntityComponent(_LOGGER, DOMAIN, hass)

    _LOGGER.info("Loading platforms...")
    for platform_conf in domain_config:
        platform = platform_conf.get("platform")
        if platform:
            try:
                # Dynamically import the platform module
                platform_module = import_module(f".{platform}", package="custom_components.processor")

                # Call the async_setup_platform function if it exists
                if hasattr(platform_module, "async_setup_platform"):
                    await platform_module.async_setup_platform(
                        hass,
                        config,
                        component.async_add_entities,  # Correctly add entities
                        platform_conf
                    )
                    _LOGGER.info(f"Successfully loaded platform: {platform}")
                else:
                    _LOGGER.warning(f"Platform {platform} does not have async_setup_platform.")
            except ImportError as e:
                _LOGGER.error(f"Failed to import platform {platform}: {e}")

    _LOGGER.info("Finished loading platforms.")
    return True


class ProcessorDevice(Entity):
    def __init__(self, hass, config):
        self.hass = hass
        self._name = config.get('name', 'Unnamed Device')
        self._unique_id = self.name
        self.log = logging.getLogger(__name__ + '.' + self.name)
        self.log.info(f"Init Processor Device: {self._unique_id}")

    def process(self, **kwargs):
        return None


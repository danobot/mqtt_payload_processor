from custom_components.processor import DOMAIN
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'mqtt_code'
""" fdsf """

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up climate entities."""
    _LOGGER.info("mqtt_code/__init__.py - async_setup" + str(config))
    component = hass.data[DOMAIN] = EntityComponent(
        _LOGGER, DOMAIN, hass)
    await component.async_setup(config)
    return True



import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from custom_components.processor.mqtt_code import DeviceEntity, MqttButton
from homeassistant.core import HomeAssistant

# Example device configuration from your YAML
TEST_CONFIG = {
    "name": "Office Wall Panel",
    "type": "panel",
    "mappings": {
        "wp-spare-btn-1": {
            "type": "button",
            "payload": 13053618,
            "callback": True,
            "actions": {
                "default": [{"service_template": "switch.toggle", "entity_id": "switch.office_standby_power_switch"}]
            }
        },
        "wp-spare-btn-2": {
            "type": "button",
            "payload": 13053624,
            "callback": False,
            "actions": {
                "default": [{"service_template": "script.turn_on_silvia"}]
            }
        },
        "wp-spare-btn-3": {
            "type": "button",
            "payload": 13053620,
            "callback": True,
            "actions": {
                "default": [{"service_template": "script.unmapped_function"}]
            }
        },
        "wp-spare-btn-1-2": {
            "type": "button",
            "payload": 13053626,
            "callback": True,
            "actions": {
                "default": [{"service_template": "script.unmapped_function"}]
            }
        }
    }
}

# -------------------
# 🔧 Test Fixtures
# -------------------

@pytest.fixture
def hass():
    """Mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)

@pytest.fixture
async def device_entity(hass):
    """Fixture to create a DeviceEntity with test config."""
    entity = DeviceEntity(hass, TEST_CONFIG)
    await entity.async_added_to_hass()
    return entity

@pytest.fixture
async def mqtt_button(hass, device_entity):
    """Fixture to create an MqttButton inside the DeviceEntity."""
    mapping_name = "wp-spare-btn-1"
    button_config = TEST_CONFIG["mappings"][mapping_name]
    button = MqttButton(hass, mapping_name, button_config, device_entity)
    await button.async_added_to_hass()
    return button

# -------------------
# 🔍 DeviceEntity Tests
# -------------------

@pytest.mark.asyncio
async def test_device_entity_creation(device_entity):
    """Test that the DeviceEntity is created with correct attributes."""
    assert device_entity.name == "Office Wall Panel"
    assert device_entity.state == "ready"
    assert device_entity.available
    assert isinstance(device_entity._mappings, list)
    assert len(device_entity._mappings) == 4  # Ensure all mappings are added

@pytest.mark.asyncio
async def test_device_async_update(device_entity):
    """Test async update method of DeviceEntity."""
    await device_entity.async_update()
    assert device_entity.state == "online"

@pytest.mark.asyncio
async def test_device_added_to_hass(device_entity):
    """Test that async_added_to_hass is called properly."""
    await device_entity.async_added_to_hass()
    assert device_entity.state == "ready"

# -------------------
# 🔍 MqttButton Tests
# -------------------

@pytest.mark.asyncio
async def test_mqtt_button_creation(mqtt_button):
    """Test that the MqttButton is initialized correctly."""
    assert mqtt_button.name == "wp-spare-btn-1"
    assert mqtt_button.state == "setting up"
    assert isinstance(mqtt_button.payloads_on, list)
    assert mqtt_button.payloads_on == [13053618]

@pytest.mark.asyncio
async def test_mqtt_button_message_handling(mqtt_button):
    """Test that the MqttButton handles MQTT messages correctly."""
    message = MagicMock()
    message.payload = "13053618"

    await asyncio.wait_for(mqtt_button.message_received(message), timeout=5)

    assert mqtt_button.last_payload == "13053618"
    assert mqtt_button.last_action == "on"
    assert mqtt_button.extra_state_attributes["payload"] == "13053618"

@pytest.mark.asyncio
async def test_mqtt_button_update_state(mqtt_button):
    """Test update_state method to ensure attributes update properly."""
    mqtt_button.update_state("13053618", "on")
    assert mqtt_button.last_action == "on"
    assert mqtt_button.extra_state_attributes["payload"] == "13053618"

@pytest.mark.asyncio
async def test_mqtt_button_added_to_hass(mqtt_button):
    """Test that async_added_to_hass is properly handled."""
    await mqtt_button.async_added_to_hass()
    assert mqtt_button.state == "ready"

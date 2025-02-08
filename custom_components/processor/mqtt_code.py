import logging
import json
import hashlib
from datetime import datetime
from homeassistant.util import dt
from custom_components.processor import ProcessorDevice
from homeassistant.helpers.entity import Entity
import homeassistant.util.uuid as uuid_util
from custom_components.processor.yaml_scheduler import TimeSchedule, Mapping
from homeassistant.components import mqtt
VERSION = '3.1.1'

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'processor'
DEFAULT_ACTION = 'default'
CONTEXT_ID_CHARACTER_LIMIT = 26
CONF_TOPIC = 'topic'
DEFAULT_TOPIC = '/rf/'
ACTION_ON = 'on'
ACTION_OFF = 'off'
TYPE_WALLPANEL = 'panel'
DEFAULT_ACTION = 'default'
JSON_VALUE_ATTRIBUTE = 'value'
CONTEXT_ID_CHARACTER_LIMIT = 26
DOMAIN_SHORT = "device"
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the MQTT Code platform."""
    _LOGGER.info("Setting up mqtt_code platform with discovery_info: %s", discovery_info)

    if discovery_info is None:
        _LOGGER.warning("No discovery info provided. Skipping setup.")
        return

    topic = discovery_info.get('topic')
    entities = []
    for entity_conf in discovery_info.get('entities', []):
        entity = DeviceEntity(hass, entity_conf)
        await entity.subscribe_mappings_to_mqtt(mqtt, topic, hass)
        _LOGGER.debug(f"Created entity: {entity.name} with topic: {topic}")
        async_add_entities(entity._mappings, update_before_add=True)
        entities.append(entity)

    async_add_entities(entities, update_before_add=True)
    for entity in entities:
        await entity.async_update()


class DeviceEntity(Entity):
    """ Represents a device such as wall panel, remote or button with 1 or more RF code buttons. Container class for Entities."""
    def __init__(self, hass, args):
        # super(Device, self).__init__(hass, args)
        # Entity Fields START
        self.hass = hass
        self._name = args.get('name', 'Unnamed Device')
        self._unique_id = f"{self._name.lower().replace(' ', '_')}"
        self.entity_id = f"mqtt_code.{self._unique_id}"
        self.friendly_name = self._name
        self.may_update = True
        self._state = 'setting up'
        self._attributes = {}
        self._available = True
        # Entity Fields END
        self.log = logging.getLogger("{}.{}".format(__name__, self._unique_id))
        self.log.info(f"Setting up device {self._unique_id}")
        self._type = args.get('type', 'panel')

        self._mapping_callbacks = []
        self._mappings = []
        for key, item in args.get('mappings').items(): # for each mapping
            item['globalLogbook'] = args.get('log', False)
            item['globalCallbackScript'] = args.get('globalCallbackScript', None)
            item['globalEvent'] = args.get('globalEvent')

            m = MqttButton(hass, key, item, self)
            self.log.info(f"adding mapping {m}")
            self._mappings.append(m)

            # self.update(**{key:m.last_triggered})


        self._schedules = {}
        try:
            for key, item in args.get('schedules').items():
                self._schedules[key] = TimeSchedule(key, item, self)
                # self._schedules[key] = ScheduleFactory.create(self, key, item, self)
        except AttributeError as a:
            self.log.debug("No schedules were defined.")

        if len(self._schedules) == 0:
            self.log.debug("No schedules defined.")
        else:
            self.log.debug("Some schedules defined.")

    async def subscribe_mappings_to_mqtt(self, mqtt, topic, hass):
        for mapping in self._mappings:
            await mqtt.async_subscribe(hass, topic, mapping.message_received)
            await mapping.async_update()

    @property
    def name(self):
        return self._name


    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def available(self):
        return self._available

    @property
    def state(self):
        return self._state
    # def add_observer(self, o):
    #     self._mapping_callbacks.append(o)
    # def remove_observer(self, o):
    #     self._mapping_callbacks.remoev(o)

    # def handle_event(self, mapping):
    #     """ called by mapping when code is received, will call mapping with active schedule name """
    #     # find active schedule
    #     schedules = self.get_active_schedules()
    #     mapping.run_actions(schedules)

    def get_active_schedules(self):
        """ Determine which schedules apply currently """
        active = []
        if self._schedules is not None:
            for name, schedule in self._schedules.items():
                self.log.debug("Checking if {} is active".format(name))
                if schedule.is_active():
                    active.append(schedule.name)

        if len(active) == 0:
            active.append(DEFAULT_ACTION)
        return active

    @property
    def extra_state_attributes(self):
        """Return the state of the entity."""
        return self._attributes.copy()

    def update(self, wait=False, **kwargs):
        """ Called from different methods to report a state attribute change """
        # self.log.debug("Update called with {}".format(str(kwargs)))
        for k,v in kwargs.items():
            if v is not None:
                self.set_attr(k,v)

        if wait == False:
            self.do_update()

    def reset_state(self):
        """ Reset state attributes by removing any state specific attributes when returning to idle state """
        self.model.log.debug("Resetting state")
        att = {}

        PERSISTED_STATE_ATTRIBUTES = [
            'last_triggered_by',
            'last_triggered_at',
            'state_entities',
            'control_entities',
            'sensor_entities',
            'override_entities',
            'delay',
            'sensor_type',
            'mode'
        ]
        for k,v in self._attributes.items():
            if k in PERSISTED_STATE_ATTRIBUTES:
                att[k] = v

        self._attributes = att
        self.do_update()

    def do_update(self, wait=False, **kwargs):
        """ Schedules an entity state update with HASS """
        # _LOGGER.debug("Scheduled update with HASS")
        if self.may_update:
            self.schedule_update_ha_state(True)

    def set_attr(self, k, v):
        # _LOGGER.debug("Setting state attribute {} to {}".format(k, v))
        if k == 'delay':
            v = str(v) + 's'
        self._attributes[k] = v
        # self.do_update()
        # _LOGGER.debug("State attributes: " + str(self.attributes))
    # HA Callbacks
    async def async_update(self):
        """Simulate an update."""
        self.log.debug(f"Updating entity: {self._name}")
        self._state = "online"
        self.async_write_ha_state()  # Notify Home Assistant of state changes

    async def async_added_to_hass(self):
        """Register update dispatcher."""
        self.log.debug(f"async_added_to_hass for {self._name}")

        self.may_update = True
        self._state = "ready"
        self.schedule_update_ha_state()

        # Subscribe to MQTT topic
        # for mapping in self._mappings:
            # self.log.debug(f"subscribing mapping {mapping.device.name} {mapping.name} to mqtt topioc {self._topic}")
            # mqtt.subscribe(self.hass, self._topic, mapping.message_received)
            # await mqtt.async_subscribe(self.hass, self._topic, mapping.message_received)





class MqttButton(Mapping, Entity):
    """ Represents a single button """

    type = None

    def __init__(self, hass, name, config, device):
        super(MqttButton, self).__init__(name, config, device)
        # Entity Fields START
        self.hass = hass
        self._name = name

        self._unique_id = f"{self.device._unique_id}_{self._name.lower().replace(' ', '_').replace('-', '_')}"
        self.entity_id = f"mqtt_code_mapping.{self._unique_id}"
        self.friendly_name = f"{self.device.friendly_name} - {name}"
        self.may_update = True
        self._state = 0
        self._available = True
        self._attributes = {}
        # Entity Fields END

        self.last_payload = None
        self.last_triggered = 'never'
        self.last_action = 'none'
        self.trigger_count = 0
        self.field = None
        self.payloads_on = []
        self.payloads_off = []
    # self.alert = Alert(
    #             self.device.hass,
    #             object_id,
    #             name,
    #             watched_entity_id,
    #             alert_state,
    #             repeat,
    #             skip_first,
    #             message_template,
    #             done_message_template,
    #             notifiers,
    #             can_ack,
    #             title_template,
    #             data,
    #         )
        self.log = logging.getLogger(__name__ + '.' + self.name)
        self.log.info(f"Setting up mapping {self._unique_id}, {self.friendly_name}, {self.name}")

        # self.log.debug(f"Init Config for Mapping {name}: "  +str(config))
        # self.log.debug("Payloads: "  +str(self.payloads_on))
        if 'field' in config:
            self.field = config.get('field', None)
        if 'payload' in config:
            self.payloads_on.append(config.get('payload'))
        if 'payloads' in config:
            self.payloads_on.extend(config.get('payloads'))
        if 'payloads_on' in config:
            self.payloads_on.extend(config.get('payloads_on'))

        if 'payload_off' in config:
            self.payloads_off.append(config.get('payload_off'))
        if 'payloads_off' in config:
            self.payloads_off.extend(config.get('payloads_off'))

        self.log.debug("Payloads ON: " + str(self.payloads_on))
        self.log.debug("Payloads OFF: " + str(self.payloads_off))
        self.type = config.get('type', None)
        self.event = config.get('event', False)
        self.callback = config.get('callback', False)
        self.callback_script = config.get('callback_script', False)
        self.globalCallbackScript = config.get('globalCallbackScript', False)
        self.log_events = config.get('globalLogbook', False) or config.get('log', False)
        self.globalEvent = config.get('globalEvent', False)

        self._always_active = False
        self.log.debug("self.device.update")
        self.device.update(**{self.name:self.last_triggered})
        self.log.debug(f"self.callback_script: {self.callback_script}")





    def process(self, payload):
        value = payload
        if payload[0] in ["{", "["]:
            j = json.loads(payload)
            # self.log.debug("JSON payload: " + str(j))
            # self.log.debug("field: " + str(self.field))
            # value = j[JSON_VALUE_ATTRIBUTE]
            if self.field is not None and self.field in value:
                value = str(j[self.field])
            elif JSON_VALUE_ATTRIBUTE in value:
                value = str(j[JSON_VALUE_ATTRIBUTE])
            else:
                self.log.warning("Payload does not contain field {} or default name 'value'.".format(self.field))

        else:
            value = str(value)
        # self.log.debug("Comparisng extracted value from payload (%s)" % (str(value)))
        # single payload defined
        # for k in j.keys():
            # self.log.debug("%s %s" % (k, j[k]))
        # self.log.debug("Is %s a match for %s?" % (value, self.name))
        for p in self.payloads_on:
            if  str(p) == value:
                self.last_payload = p
                self.log.info("Processing ON payload: %s" % (p))
                self.handleRFCode(ACTION_ON)
                self.update_state(payload, ACTION_ON)
                break

        for p in self.payloads_off:
            if str(p) == value:
                self.last_payload = p
                self.log.info("Processing OFF payload: %s" % (p))
                self.handleRFCode(ACTION_OFF)
                self.update_state(payload, ACTION_OFF)
                break

    def message_received(self, message):
        """Handle new MQTT messages."""

        # self.log.debug("Message received: " + str(message))

        self.process(message.payload)



    def update_state(self, payload, action):
        # self.log.debug(f"name={self.name}, payload={payload},action={action}")

        self.last_action = action
        self.last_triggered = dt.now()
        self.device.update(**{self.name:self.last_triggered})

        name_hash = hashlib.sha1(self.device.entity_id.encode("UTF-8")).hexdigest()[:6]
        unique_id = uuid_util.random_uuid_hex()
        context_id = f"{DOMAIN_SHORT}_{name_hash}_{unique_id}"
        # Restrict id length to database field size
        context_id = context_id[:CONTEXT_ID_CHARACTER_LIMIT]

        # self.entity_id = f"{DOMAIN}.{self._unique_id}"
        if self.log_events:
            log_data= {
                'name':  str(self.name) ,
                'message': " was triggered by RF code " +  str(payload),
                'entity_id': context_id,
                'domain': 'processor'
            }
            # if self.type == 'button':
            #     log_data['message'] = 'was pressed'

            # if self.type == 'motion':
            #     log_data['message'] = 'was activated'

            self.device.hass.services.call('logbook', 'log', log_data)
        self.update_attributes()
        self.schedule_update_ha_state(True)



    def handleRFCode(self, action):
        # self.hass.states.set(DOMAIN + '.last_triggered_by', self.name)
        # hass.states.set('rf_processor.last_triggered_time', time.localtime(time.time()))
        # self.log.debug("event: " + str(self.event))
        # self.log.debug("globalEvent: " + str(self.globalEvent))
        self.last_action = action
        self.last_triggered = dt.now()
        self.log_execution()

        schedules = self.device.get_active_schedules()
        self.run_actions(schedules)

        if self.event or self.globalEvent:
            self.log.debug("Sending event.")
            self.device.hass.bus.fire(self.name, {
                'state': action
            })

        if self.globalCallbackScript is not None and self.callback:
            self.log.info("Running global callback script: " + self.globalCallbackScript)
            self.device.hass.services.call('script', 'turn_on', {'entity_id': self.globalCallbackScript})

        if self.callback_script:
            device, script = self.callback_script.split('.')
            self.log.info("Running device callback script: " + script)
            self.device.hass.services.call('script', 'turn_on', {'entity_id': self.callback_script})

    @property
    def should_poll(self):
        return False

    @property
    def device_class(self) -> str:
        """Define the device class for a numeric entity."""
        return "measurement"
    
    @property
    def unit_of_measurement(self) -> str:
        """Return the unit for the counter."""
        return "count"
    def log_execution(self):
        self.trigger_count += 1

    def update_attributes(self):

        new_attr = {
            'last_action': self.last_action,
            'payload': self.last_payload,
            'payloads_on': self.payloads_on,
            'payloads_off': self.payloads_off,
            'last_triggered': self.last_triggered,
        }
        if self.type:
            new_attr['type'] = self.type

        if self.callback_script:
            new_attr['callback_script'] = self.callback_script

        if self.callback:
            new_attr['callback'] = self.callback

        if self.globalCallbackScript is not None:
            new_attr['global_callback'] = self.globalCallbackScript
        if self.globalEvent:
            new_attr['globalEvent'] = True

        self._attributes = new_attr
        self._state = self.trigger_count

    @property
    def extra_state_attributes(self):
        """Return the state of the entity."""
        return self._attributes.copy()

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self) -> str:
        return str(self._state)


    @property
    def available(self):
        return self._available


    # HA Callbacks
    async def async_update(self):
        """Simulate an update."""
        self.log.debug(f"Updating entity: {self._name}")
        self.update_attributes()
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register update dispatcher."""
        self.log.debug(f"async_added_to_hass for {self._name}")

        self.may_update = True
        self._state = 0
        self.schedule_update_ha_state()

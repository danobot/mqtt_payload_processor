# MQTT Payload Processor for Home Assistant
# Converts MQTT message payloads to Home Assistant events and callback scripts.
# Useful for storing implementation specific codes in one location and using 
# HA specific abstractions throughout the configuration.
# E.g. RF codes, Bluetooth ids, etc.

# Documentation:    https://github.com/danobot/mqtt_payload_processor
# Version:          v2.0.2

import homeassistant.loader as loader
import logging
import asyncio
import json
from datetime import datetime,  timedelta, date, time
from homeassistant.helpers.entity import Entity
from custom_components.processor import ProcessorDevice
from homeassistant.util import dt
from homeassistant.core import HomeAssistant as hass
from homeassistant.components.script import ScriptEntity
from homeassistant.loader import bind_hass
import homeassistant.helpers.script as script 
from custom_components.processor.yaml_scheduler import Action, Scheduler, TimeSchedule, Mapping
# from datetimerange import DateTimeRange

VERSION = '2.0.2'

DEPENDENCIES = ['mqtt']
# REQUIREMENTS = ['datetimerange']
CONF_TOPIC = 'topic'
DEFAULT_TOPIC = '/rf/'
ACTION_ON = 'on'
ACTION_OFF = 'off'
TYPE_WALLPANEL = 'panel'
DEFAULT_ACTION = 'default'
_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    from homeassistant.components import mqtt
    entities = []

    # mqtt = loader.get_component(hass, 'mqtt')
    topic = config.get('topic', DEFAULT_TOPIC)
    _LOGGER.info("Platform Config:" + str(config))

    for v in config['entities']:
        _LOGGER.info("Entity: " + str(v))
        v['globalCallbackScript'] = config.get('callback_script', None)
        v['globalEvent'] = config.get('event')

        m = None
        m = Device(v, mqtt, topic, hass)

        # must be done here because self.hass inside `m` is None for some reason
        # (even though it inherits from `Entity`)
        # 
        
        entities.append(m)

    
    add_entities(entities)

    return True


class Device(ProcessorDevice):
    """ Represents a device such as wall panel, remote or button with 1 or more RF code buttons. Container class for Entities."""
    def __init__(self, args, mqtt, topic, hass):
        self.log = logging.getLogger("{}.device.{}".format(__name__, args.get('name', 'unnamed')))

        self._name = args.get('name', 'Unnamed Device')
        self._type = args.get('type', 'panel')
        self.may_update = False
        self._state = 'setting up'
        self._mapping_callbacks = []
        self.attributes = {}
        self._mappings = []
        for key, item in args.get('mappings').items(): # for each mapping
            item['globalLogbook'] = args.get('log', False)
            item['globalCallbackScript'] = args.get('globalCallbackScript', None)
            item['globalEvent'] = args.get('globalEvent')

            m = MqttButton(key, item, self)
            self._mappings.append(m)
            mqtt.subscribe(hass, topic, m.message_received)
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
        
    @property
    def state(self):
        return self._state
    @property
    def name(self):
        """Return the state of the entity."""
        return self._name
    # def add_observer(self, o):
    #     self._mapping_callbacks.append(o)
    # def remove_observer(self, o):
    #     self._mapping_callbacks.remoev(o)

    def handle_event(self, mapping):
        """ called by mapping when code is received, will call mapping with active schedule name """
        # find active schedule
        schedules = self.get_active_schedules()
        mapping.run_actions(schedules)

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
    def state_attributes(self):
        """Return the state of the entity."""
        return self.attributes.copy()
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
        for k,v in self.attributes.items():
            if k in PERSISTED_STATE_ATTRIBUTES:
                att[k] = v

        self.attributes = att
        self.do_update()

    def do_update(self, wait=False,**kwargs):
        """ Schedules an entity state update with HASS """
        # _LOGGER.debug("Scheduled update with HASS")
        if self.may_update:
            self.async_schedule_update_ha_state(True)

    def set_attr(self, k, v):
        # _LOGGER.debug("Setting state attribute {} to {}".format(k, v))
        if k == 'delay':
            v = str(v) + 's'
        self.attributes[k] = v
        # self.do_update()
        # _LOGGER.debug("State attributes: " + str(self.attributes))
    # HA Callbacks
    async def async_added_to_hass(self):
        """Register update dispatcher."""
        self.may_update = True
        self._state = "ready"
        self.do_update()



# class Mapping:
#     def __init__(self, name, config, device):
#         self.name = name
#         self.device = device
#         self.log = logging.getLogger("{}.mappings.{}".format(device.log.name, name))
#         self._schedule_actions = {}
#         try:
#             for key, item in config.get('actions').items(): 
#                 self._schedule_actions[key] = Action(self, key, item)
#         except AttributeError as a:
#             self.log.debug("No schedule actions defined.")

#     def run_actions(self, schedule_names):
#         self.log.debug(schedule_names)
#         self.log.debug(self._schedule_actions)
#         for s in schedule_names:
#             if s in self._schedule_actions.keys():
#                 for name, action in self._schedule_actions.items():
#                     action.execute(s) # method will only run actions if schedule names match
        # If no actions match at the current time:
        # self.log.error("Schedule name {} is not defined.".format(s.name))
        # if 'default' in self._schedule_actions:
        #     self.log.debug("Executing default action instead")
        #     self._schedule_actions['default'].execute(s)


class MqttButton(Mapping):
    """ Represents a single button """

    type = None

    def __init__(self, name, config, device):
        super(MqttButton, self).__init__(name, config, device)
        self.last_payload = None
        self.last_triggered = 'never'
        self.last_action = 'none'
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
        self.name = name
        # self.log = logging.getLogger(__name__ + '.' + self.name)
        self.log.debug("Init Config: "  +str(config))
        self.log.debug("Payloads: "  +str(self.payloads_on))
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
        self.device.update(**{self.name:self.last_triggered})



    # @property
    # def device_state_attributes(self):
    #     return {
    #         'last_triggered': self.last_triggered,
    #         'last_payload': self.last_payload,
    #         'last_action': self.last_action,
    #         'payloads_on': self.payloads_on,
    #         'payloads_off': self.payloads_off,
    #         'callback': self.callback,
    #         'callback_script': self.callback_script,
    #         'global_callback_script': self.globalCallbackScript,
    #         'event': self.event,
    #         'global_event': self.globalEvent,
    #         'type': self.type
    #     }

    def process(self, payload):
        j = json.loads(payload)
        # self.log.debug("Called process on %s %s" % (str(j), str(dir(j))))
        # single payload defined
        # for k in j.keys():
            # self.log.debug("%s %s" % (k, j[k]))
        value = j["value"]
        # self.log.debug("Is %s a match for %s?" % (value, self.name))
        for p in self.payloads_on:
            if int(p) == value:
                self.log.info("Processing %s on code" % (p))
                self.handleRFCode(ACTION_ON)
                self.update_state(payload, ACTION_ON)
                break

        for p in self.payloads_off:
            if int(p) == value:
                self.log.info("Processing %s off code" % (p))
                self.handleRFCode(ACTION_OFF)
                self.update_state(payload, ACTION_OFF)
                break

    def message_received(self, message):
        """Handle new MQTT messages."""

        # self.log.debug("Message received: " + str(message))

        self.process(message.payload)


    def update_state(self, payload, action):
        self.last_payload = payload
        self.last_action = action
        self.last_triggered = dt.now()
        self.log.debug("name is " + self.name)
        self.device.update(**{self.name:self.last_triggered})
        if self.log_events:
            log_data= {
                'name':  str( self.name) ,
                'message': " was triggered by RF code " +  str(payload),
                'entity_id': self.device.entity_id,
                'domain': 'processor'
            }
            # if self.type == 'button':
            #     log_data['message'] = 'was pressed'

            # if self.type == 'motion':
            #     log_data['message'] = 'was activated'

            self.device.hass.services.call('logbook', 'log', log_data)
        # self.async_schedule_update_ha_state(True)



    def handleRFCode(self, action):
        # self.hass.states.set(DOMAIN + '.last_triggered_by', self.name)
        # hass.states.set('rf_processor.last_triggered_time', time.localtime(time.time()))
        # self.log.debug("event: " + str(self.event))
        # self.log.debug("globalEvent: " + str(self.globalEvent))
        self.device.handle_event(self)
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
        if self.globalEvent:
            state['globalEvent'] = True

        return state




# class WallPanel(Device):


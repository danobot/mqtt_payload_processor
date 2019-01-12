# MQTT Payload Processor for Home Assistant
# Converts MQTT message payloads to Home Assistant events and callback scripts.
# Useful for storing implementation specific codes in one location and using 
# HA specific abstractions throughout the configuration.
# E.g. RF codes, Bluetooth ids, etc.

# Documentation:    https://github.com/danobot/mqtt_payload_processor
# Version:          v1.0.0

import homeassistant.loader as loader
import logging
import asyncio
from datetime import datetime,  timedelta, date, time
from homeassistant.helpers.entity import Entity
from custom_components.processor import ProcessorDevice
from homeassistant.util import dt
from homeassistant.core import HomeAssistant as hass
from homeassistant.components.script import ScriptEntity
from homeassistant.loader import bind_hass
import homeassistant.helpers.script as script 
# from datetimerange import DateTimeRange

VERSION = '1.0.0'

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
    
    entities = []

    mqtt = loader.get_component(hass, 'mqtt')
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
        self._mapping_callbacks = []

        self._mappings = []
        for key, item in args.get('mappings').items(): # for each mapping
            m = MqttButton(key, item, self)
            self._mappings.append(m)
            mqtt.subscribe(hass, topic, m.message_received)


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
        for name, schedule in self._schedules.items():
            self.log.debug("Checking if {} is active".format(name))
            if schedule.is_active():
                active.append(schedule.name)
        
        if len(active) == 0:
            active.append(DEFAULT_ACTION)
        return active
    
class Action:
    """ What needs to happen for a given schedule. """
    def __init__(self, mapping, name, args):
        self.mapping = mapping
        # super(Action,self).__init__(self.hass,'processor-action' + name,name,args)
        self.log = logging.getLogger("{}.actions.{}".format(mapping.log.name, name))
        self.log.info("Creating action " + name)
        if 'name' is None:
            self.log.error("Missing name in Action")
        self.schedule_name = name
        self.log.debug("Script Sequence: " + str(args))
        # component = loader.get_component('script')

        # async def service_handler(service):
        #     """Execute a service call to script.<script name>."""
        #     entity_id = ENTITY_ID_FORMAT.format(service.service)
        #     script = component.get_entity(entity_id)
        #     if script.is_on:
        #         _LOGGER.warning("Script %s already running.", entity_id)
        #         return
        #     await script.async_turn_on(variables=service.data,
        #                             context=service.context)

        # object_id = 'processor-action' + name
        # alias = name
        # self.script = ScriptEntity(hass, object_id, alias, args)
        # hass.services.async_register(
        #     'script', object_id, service_handler, schema=vol.Schema(dict))
        self._script_config = args
#         await component.async_add_entities([self.script])
        
        
        # self.script = Script(hass, args, name, self.async_update_ha_state)

    def execute(self, schedule):
        if self.schedule_name == schedule:
            self.log.debug("Executing actions in Action {}".format(self.schedule_name)) 
            script.call_from_config(self.mapping.device.hass, self._script_config)

            



class ScheduleFactory:
    """ Creates Schedule based on platform parameter """
    def create(self,name, args,  device):
        if not 'platform' in args:
            _LOGGER.error("ScheduleFactory cannot create schedule because platform is unspecified.")

        _platform = args.get('type')
        if _platform == 'time':
            return TimeSchedule(name, args, device)

class Schedule:
    """ The schedule itself to check which schedule applies """

    def __init__(self, device, name, args):
        _LOGGER.info("{}.schedules.{}".format(device.log.name, name))
        self._name = name
        self.log = logging.getLogger("{}.schedules.{}".format(device.log.name, name))
        self.log.debug("Initialising Schedule " + name)

    @property
    def name(self):
        return self._name

    def is_active(self):
        return False

class TimeSchedule(Schedule):
    TIME_START = 'start_time'
    TIME_END = 'end_time'
    def __init__(self, name, args, device):
        super(TimeSchedule, self).__init__(device, name, args)
        self.log.debug("Initialising TimeSchedule")
        if self.TIME_START in args and self.TIME_END in args:
            self._start_time = dt.parse_time(args.get(self.TIME_START))
            self._end_time = dt.parse_time(args.get(self.TIME_END))
            self.log.debug("start: {}, end: {}".format(self._start_time,self._end_time))
        else:
            self.log.error("TimeSchedule requires a start and end time.")

    def is_active(self):
        e = self.now_is_between(self._start_time, self._end_time)
        self.log.debug("Is now between {} and {}? {}".format(self._start_time, self._end_time,e))
        return e



    def now_is_between(self, start, end, x=None):
        if x is None:
            x = datetime.time(datetime.now())

        today = date.today()
        self.log.debug("Current time" + str(x))
        start = datetime.combine(today, start)
        end = datetime.combine(today, end)
        x = datetime.combine(today, x)
        if end <= start:
            self.log.debug("Bumping now_is_between input start time to tomorrow")
            end += timedelta(1) # tomorrow!
        if x <= start:
            x += timedelta(1) # tomorrow!
        return start <= x <= end

class Mapping:
    def __init__(self, name, config, device):
        self.device = device
        self.log = logging.getLogger("{}.mappings.{}".format(device.log.name, name))
        self._schedule_actions = {}
        for key, item in config.get('actions').items(): 
            self._schedule_actions[key] = Action(self, key, item)

        if len(self._schedule_actions) == 0:
            self.log.debug("No schedule actions defined.")
        else:
            self.log.debug("Many actions defined.")

    def run_actions(self, schedule_names):
        self.log.debug(schedule_names)
        self.log.debug(self._schedule_actions)
        for s in schedule_names:
            if s in self._schedule_actions.keys():
                for name, action in self._schedule_actions.items():
                    action.execute(s) # method will only run actions if schedule names match
        # If no actions match at the current time:
        # self.log.error("Schedule name {} is not defined.".format(s.name))
        # if 'default' in self._schedule_actions:
        #     self.log.debug("Executing default action instead")
        #     self._schedule_actions['default'].execute(s)


class MqttButton(Mapping):
    """ Represents a single button """

    type = None
    name = None
    last_payload = None
    last_triggered = 'never'
    last_action = 'none'
    def __init__(self, name, config, device):
        super(MqttButton, self).__init__(name, config, device)

        self.payloads_on = []
        self.payloads_off = []
    
        self.name = config.get('name', name)

        self._unique_id = self.name
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
        self.log_events = config.get('log', False)
        self.event = config.get('event', False)
        self.callback = config.get('callback', False)
        self.callback_script = config.get('callback_script', False)
        self.globalCallbackScript = config.get('globalCallbackScript', False)
        self.globalEvent = config.get('globalEvent', False)
        
        self._always_active = False
        



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

    def message_received(self, topic, payload, qos):
        """Handle new MQTT messages."""

        # self.log.debug("Message received: " + str(payload))

        self.process(payload)

    def process(self, payload):
        
        # self.log.debug("Called process on {}".format(self.name))
        # # single payload defined

        self.log.debug("Is {} a match in {}?".format(payload, str(self.payloads_on)))
        for p in self.payloads_on:
            if int(p) == int(payload):
                self.log.debug("Processing {} on code".format(p))
                self.handleRFCode(ACTION_ON)
                self.update_state(payload, ACTION_ON)
                break

        for p in self.payloads_off:
            if int(p) == int(payload):
                self.log.debug("Processing {} off code".format(p))
                self.handleRFCode(ACTION_OFF)
                self.update_state(payload, ACTION_OFF)
                break

    def update_state(self, payload, action):
        self.last_payload = payload
        self.last_action = action
        self.last_triggered = dt.now()
        # self.async_schedule_update_ha_state(True)



    def handleRFCode(self, action):
        # self.hass.states.set(DOMAIN + '.last_triggered_by', self.name)
        # hass.states.set('rf_processor.last_triggered_time', time.localtime(time.time()))
        self.log.debug("event: " + str(self.event))
        self.log.debug("globalEvent: " + str(self.globalEvent))
        self.device.handle_event(self)
        if self.event or self.globalEvent:
            self.hass.bus.fire(self.name, {
                'state': action
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
        if self.globalEvent:
            state['globalEvent'] = True

        return state




# class WallPanel(Device):


import logging;
from datetime import datetime,  timedelta, date, time
import homeassistant.helpers.script as script
from homeassistant.core import Context
from . import DOMAIN
_LOGGER = logging.getLogger(__name__)
from homeassistant.util import dt
VERSION='2.0.2'
class Scheduler:

  def __init__(self, yaml):
    self.log = logging.getLogger(__name__)
    self._schedules = {}
    try:
      for key, item in yaml.items(): 
        self._schedules[key] = TimeSchedule(key, item, self)
          # self._schedules[key] = ScheduleFactory.create(self, key, item, self)
    except AttributeError as a:
      self.log.debug("No schedules were defined.")

    if len(self._schedules) == 0:
      self.log.debug("No schedules defined.")
    else:
      self.log.debug("Some schedules defined.")

  def addSubscriber(schedule, callback):
    if schedule not in self._schedules:
      self.log.error("Schedule not defined!")
  
  def run(self):
      self.log.debug(self._schedules)
      self.log.debug(self._schedule_actions)
      for s in self._schedules:
          if s in self._schedule_actions.keys():
              for name, action in self._schedule_actions.items():
                  action.execute(s) # method will only run actions if schedule names match

class Action:
    """ What needs to happen for a given schedule. """
    def __init__(self, mapping, name, args):
        self.mapping = mapping
        # super(Action,self).__init__(self.hass,'processor-action' + name,name,args)
        self.log = logging.getLogger("{}.actions.{}".format(mapping.log.name, name))
        self.log.info("Creating action " + name)
        if name is None:
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

    def execute(self, schedule): ## passed in call-back function
        if self.schedule_name == schedule:
            self.log.debug("Executing actions in Action {}".format(self.schedule_name)) 
            try:
                # self.log.error(str(dir(script)))
                # self.log.error(str(dir(script.service)))
                s = script.Script(self.mapping.device.hass, self._script_config, self.schedule_name, DOMAIN)
                context = Context(parent_id="device.%s" % (self.mapping.device.name), id="actions.{}".format( self.schedule_name))
                s.run(context=context)
            except Exception as e:  
                self.log.error("Error calling supplied script: " + str(e))
                raise e
            



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
      self.name = name
      self.device = device
      self.log = logging.getLogger("{}.mappings.{}".format(device.log.name, name))
      self._schedule_actions = {}
      try:
        for key, item in config.get('actions').items(): 
          self._schedule_actions[key] = Action(self, key, item)
      except AttributeError as a:
        self.log.debug("No schedule actions defined.")

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

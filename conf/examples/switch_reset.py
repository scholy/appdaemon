import appdaemon.appapi as appapi
import shelve

#
# App to reset input_boolean, input_select, input_slider to previous values after HA restart
#
# Args:
#
#delay - amount of time after restart to set the switches
# 
#
# Release Notes
#
# Version 1.0:
#   Initial Version

class SwitchReset(appapi.AppDaemon):

  def initialize(self):
    
    self.device_db = shelve.open(self.args["file"])
    self.listen_event(self.ha_event, "ha_started")
    self.listen_event(self.appd_event, "appd_started")
    self.listen_state(self.state_change, "input_boolean")
    self.listen_state(self.state_change, "input_select")
    self.listen_state(self.state_change, "input_slider")
    self.log_notify("Finished Init")
       
  def ha_event(self, event_name, data, kwargs):
    self.log_notify("Home Assistant start")
    self.run_in(self.set_switches, self.args["delay"])
    
  def appd_event(self, event_name, data, kwargs):
    self.log_notify("AppDaemon start")
    self.run_in(self.set_switches, self.args["delay"])

  def state_change(self, entity, attribute, old, new, kwargs):
    #self.log_notify("State change: {} to {}".format(entity, new))
    self.device_db[entity] = new
  
  def set_switches(self, kwargs):
    self.log_notify("Setting switches")
    # Find out what devices are avaiable.
    # If we don't know about it initialize, if we do set the switch appropriately
    state = self.get_state()
    for entity in state:
      type, id = entity.split(".")
      if type == "input_boolean" or type == "input_select" or type == "input_slider":
        self.log_notify("Checking {}".format(entity))
        if entity in self.device_db:
          if self.device_db[entity] != state[entity]["state"]:
            self.log_notify("  -> Found, setting value to {} (was {})".format(self.device_db[entity], state[entity]["state"]))
            new_state = self.set_state(entity, state = self.device_db[entity])
          else:
            self.log_notify("  -> Found, value is correct({})".format(state[entity]["state"]))
        else:
          self.log_notify("  -> New entity, setting value to current state ({})".format(state[entity]["state"]))
          self.device_db[entity] = state[entity]["state"]
  
  def log_notify(self, message, level = "INFO"):
    if "log" in self.args:
      self.log(message)
    if "notify" in self.args:
      self.notify(message)
# Introduction

# Getting Stated
To get started, you need to have some kind of device that emits specific payloads on an MQTT topic that you want to convert to Home Assistant events. My use case is integration with OpenMQTTGateway where RF payloads are sent on a specific MQTT topic.

Add the following to your configuration:
```yaml


mqtt_topic_processor:
  topic: /rf/all
  entities: 
    - name: wp-lr-btn-1
      type: button
      payload: 5842324
    - name: wp-lr-btn-2
      type: button
      payload: 5842322
```

This configuration listens for RF codes on the specified MQTT topic and generates events named after the `name` attribute when the corresponding payload is received. The `type` attrbute only adds a custom icon in the event log for now. Supported options so far are `button` and `motion`.

You will likely have a large number of defined devices as they add up quickly. A three-button RF wall panel sends out 6 different codes depending on what combination of buttons is pressed. You can split your rf_code definition into a separate file like this:

```yaml 
mqtt_topic_processor:
  topic: /rf/all
  entities: !include rf_codes.yaml

```

Where the file has the following contents:

```yaml
- name: wp-lr-btn-1
  type: button
  payload: 5842324
- name: wp-lr-btn-2
  type: button
  payload: 5842322
```
# Configuration

## Callback Scripts
You can define a script to be called as a sort of callback function. I use this to emit a short sound when specific buttons are pressed. (Sometimes the automation triggered by the button does not have immediate feedback). By default, the top level script is called if (and only if) the device declares `callback: true`.

You can define device-level callback scripts as well. Use the `callback` attribute to control whether or not the global callback script is executed when a local script is defined.
```yaml

mqtt_topic_processor:
  topic: /rf/all
  callback_script: script.buzz_short
  entities: 
    - name: wp-lr-btn-1
      type: button
      payload: 5842324
      callback: true        # uses global callback script
    - name: wp-lr-btn-2
      type: button
      payload: 5842322
      callback_script: script.custom_script
```

In addition to scripts, you can build automations that are triggered by the event emitted by the component when certain payloads are received. For example:

```yaml
- alias: WP BR Button 1
  hide_entity: yes
  trigger:
    platform: event
    event_type: wp-lr-btn-1
  action:
    - service: light.toggle
      entity_id:
        - light.living_room_floor_lamp
```

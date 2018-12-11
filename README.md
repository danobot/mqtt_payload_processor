# Introduction
Custom Home Assistant component that converts MQTT message payloads to events and callback functions for consumption in automations. Provides a neat way to decouple implementation specific payloads (such as RF codes) from your Home Assistant configuration.

## How does it work?
You need have some kind of device that emits specific payloads on an MQTT topic that you want to convert to Home Assistant events. My use case is integration with OpenMQTTGateway where RF payloads are sent on a specific MQTT topic.

For example, an RF motion sensor, door sensor and wall button panel may send the following messages on `/rf/all`:

```
/rf/all 121330
/rf/all 163562
/rf/all 136566
```

Each payload is unique to a device.

This component allows you to name and define these devices (including their respective RF codes) in one central location. The rest of your Home Assistant configuration then refers to events and callback scripts instead. (This way your RF codes are not duplicated and used throughout the configuration.)

My examples are specific to RF devices, but you can use this component in any situation where implementation specific data is sent on an MQTT topic and you want to add a layer of abstraction on top of it.

# Getting Stated

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

This configuration listens for RF codes on the specified MQTT topic and generates events named after the `name` attribute when the corresponding payload is received. The `type` attribute only adds a custom icon in the event log for now. Supported options so far are `button` and `motion`.

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

# State Tracking
The component creates entities for each device defined in the configuration. An example state is shown below:
```json
{
    'last_triggered': '2018-11-27T10:47:10.640502', 
    'payload': '1268280', 
    'type': 'button', 
    'callback_script': 'script.buzz_short', 
    'global_callback': 'script.buzz_short'
}
```

# Future Enhancements
* Group multiple devices into larger entities representing the physical device.

# Automatic updates
Use the `custom_updater` component to track updates.
```yaml
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/danobot/mqtt_payload_processor/master/tracker.json
```

# Changelog
Refer to the `Changelog` file for detailed information.
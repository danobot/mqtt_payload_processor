# Introduction
Custom Home Assistant component that converts MQTT message payloads to events and callback functions for consumption in automations. Provides a neat way to decouple implementation specific payloads (such as RF codes) from your Home Assistant configuration. Define schedule specific actions to execute when a device button is triggered.

![Diagram](images/diagram.png)

# Getting Stated
The use case for this component is a little abstract and difficult to understand (i forget myself sometimes...). Please read the full documentation which gives a good introduction to what this component is about.

[Documentation](https://github.com/danobot/mqtt_payload_processor)

Once you understand the premise you will no doubt find ways to make use of this component.


Sample configuration:
```yaml

processor:
  - platform: mqtt_code
    topic: /rf/all
    callback_script: script.buzz_short      # Global Callback (Executed disabled downstream)
    event: True                             # Global event flag, overwrites local (send HA events)
    entities: 
      - name: wallpanel-button-1
        type: button
        payload: 5842324
        callback_script: script.buzz_long
      - name: wallpanel-button-2
        type: button
        payloads_on: 
          - 5842324
          - 5842325
        payloads_off: 
          - 5842333
          - 5842334
        callback: False                     # Do not call global callback, True is default

```
[Buy me a coffee to support ongoing development](https://www.gofundme.com/danobot&rcid=r01-155117647299-36f7aa9cb3544199&pc=ot_co_campmgmt_w)


#!/usr/bin/env python3

"""
checks the presence sensors
"""

import json
import logging
import requests
import paho.mqtt.client as mqtt
import os

logger = logging.getLogger(__name__)

LAST_OCCUPANCY = {
    "1": False,
    "2": False,
    "3": False,
}

TELEGRAM_TOKEN = None
TELEGRAM_CHATID = None


def check_state_changed(sensor, value):
    if sensor in LAST_OCCUPANCY:
        if LAST_OCCUPANCY.get(sensor) == value:
            return False
    LAST_OCCUPANCY[sensor] = value
    return True


def start(broker, user, passwd):
    "setup mqtt client"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(user, passwd)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, 1883, 0)
    client.loop_forever()


def on_connect(client, _userdata, _flags, rc, properties):
    """
    mqtt connection handler
    """
    if rc == 0:
        logger.debug("subscribe")
        client.subscribe("zigbee/Sonoff Presence Sensor 1/#")
        client.subscribe("zigbee/Sonoff Presence Sensor 2/#")
        client.subscribe("zigbee/Presence Sensor 1/#")
        # client.subscribe("zigbee2mqtt/#")
    else:
        logger.error("on_connect status %s", rc)


def on_message(_client, _userdata, message):
    """
    mqtt message handler
    """
    try:
        if message.topic == "zigbee/Sonoff Presence Sensor 1":
            read_prensence_payload("1", message)
        if message.topic == "zigbee/Sonoff Presence Sensor 2":
            read_prensence_payload("2", message)
        if message.topic == "zigbee/Presence Sensor 1":
            read_prensence_payload("3", message)
    except ValueError as e:
        logger.error("error on_message: %s", e)
    except Exception as e:
        logger.error("error on_message: %s", e)


def read_prensence_payload(sensor, message):
    """
    parses the mqtt message
    """
    try:
        json_data = json.loads(message.payload.decode())
        logger.warning(json_data)
        val = json_data.get("occupancy")
        if check_state_changed(sensor, val):
            send_telegram(
                f"occupancy changed {sensor}: {val}",
                TELEGRAM_TOKEN,
                TELEGRAM_CHATID,
            )
        else:
            logger.warning("ignore event")
    except json.JSONDecodeError as e:
        logger.error("decode error: %s", e)


def send_telegram(message, token, chat_id):
    """
    sends the telegram message
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    logger.warning(requests.get(url, timeout=2).json())


def read_env(varname, default=None):
    val = os.environ.get(varname, default)
    if val is None:
        raise RuntimeError(f"missing required variable: {varname}")
    return val


if __name__ == "__main__":
    mqtt_broker = read_env("MQTT_BROKER")
    mqtt_user = read_env("MQTT_USER")
    mqtt_passwd = read_env("MQTT_PASSWD")
    telegram_chatid = read_env("TELEGRAM_CHATID")
    telegram_token = read_env("TELEGRAM_TOKEN")

    TELEGRAM_CHATID = telegram_chatid
    TELEGRAM_TOKEN = telegram_token
    while True:
        start(mqtt_broker, mqtt_user, mqtt_passwd)

#!/usr/bin/env python3

"""
checks the presence sensor
"""

import argparse
import json
import logging
import requests
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

LAST_OCCUPANCY = None

TELEGRAM_TOKEN = None
TELEGRAM_CHATID = None


class ArgumentParserReadFileAction(argparse.Action):
    """
    read value from file
    """

    def __call__(self, _parser, namespace, values, _option_string=None):
        if not isinstance(values, str):
            raise argparse.ArgumentError(self, "value must be a sring")
        with open(values, "r", encoding="utf-8") as f:
            setattr(namespace, self.dest, f.readline().strip())


def start(broker, user, passwd):
    "setup mqtt client"
    client = mqtt.Client()
    client.username_pw_set(user, passwd)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, 1883, 0)
    client.loop_forever()


def on_connect(client, _userdata, _flags, rc):
    """
    mqtt connection handler
    """
    if rc == 0:
        logger.debug("subscribe")
        client.subscribe("zigbee/Sonoff Presence Sensor 1/#")
        # client.subscribe("zigbee2mqtt/#")
    else:
        logger.error("on_connect status %s", rc)


def on_message(_client, _userdata, message):
    """
    mqtt message handler
    """
    try:
        if message.topic == "zigbee/Sonoff Presence Sensor 1":
            read_prensence_payload(message)
    except ValueError as e:
        logger.error("error on_message: %s", e)
    except Exception as e:
        logger.error("error on_message: %s", e)


def read_prensence_payload(message):
    """
    parses the mqtt message
    """
    global LAST_OCCUPANCY
    try:
        json_data = json.loads(message.payload.decode())
        logger.warning(json_data)
        val = json_data.get("occupancy")
        if val != LAST_OCCUPANCY:
            LAST_OCCUPANCY = val
            send_telegram(
                f"occupancy changed: {val}",
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="presence_sensor", description="checks the presence sensor"
    )
    parser.add_argument(
        "-b", required=True, dest="mqtt_broker", help="broker name or address"
    )
    parser.add_argument("-u", required=True, dest="mqtt_user", help="username")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", dest="passwd", help="password")
    group.add_argument(
        "-pf",
        dest="passwd",
        action=ArgumentParserReadFileAction,
        help="path to file that stores a password",
    )
    # telegram
    parser.add_argument(
        "-c", required=True, dest="telegram_chatid", help="telegram chatid"
    )
    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument(
        "-t",
        dest="telegram_token",
        action=ArgumentParserReadFileAction,
        help="path to file that stores the telegram token",
    )
    args = parser.parse_args()
    TELEGRAM_CHATID = args.telegram_chatid
    TELEGRAM_TOKEN = args.telegram_token
    while True:
        start(args.mqtt_broker, args.mqtt_user, args.passwd)

#!/usr/bin/env python3

import argparse
import configparser
import datetime
import time

import requests

from twilio.rest import Client
from utils import check_twilio_version


check_twilio_version()

config = configparser.ConfigParser()
config.read("config.cfg")

TO_NUMBER = config.get("Twilio", "TO_NUMBER")
FROM_NUMBER = config.get("Twilio", "FROM_NUMBER")
TWILIO_URL = config.get("Twilio", "TWILIO_URL")
ACCOUNT_SID = config.get("Twilio", "ACCOUNT_SID")
AUTH_TOKEN = config.get("Twilio", "AUTH_TOKEN")
CALL_TIMEOUT = config.getint("Twilio", "CALL_TIMEOUT")
GRACE_PERIOD = config.getint("Twilio", "GRACE_PERIOD")
RETRIAL_INTERVAL = config.getint("Twilio", "RETRIAL_INTERVAL")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

STORES = {
    "WACR": {
        "name": "Walnut Creek",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R014",
    },
    "SFUS": {
        "name": "San Francisco Union Square",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R075",
    },
    "SACR": {
        "name": "Sacramento Arden Fair",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R070",
    },
    "ROSE": {
        "name": "Roseville",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R298",
    },
    "4THS": {
        "name": "4th Street (Berkeley)",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R414",
    },
    "BAYS": {
        "name": "Bay Street (Emeryville)",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R057",
    },
    "STPL": {
        "name": "Stoneridge Mall (Pleasanton)",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R101",
    },
    "CHEST": {
        "name": "Chestnut Street (SF)",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R217",
    },
    "STSF": {
        "name": "Stonestown (SF)",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R033",
    },
    "COMA": {
        "name": "Corte Madera",
        "url": "http://www.apple.com/shop/retail/pickup-message?parts.0="
        "MWP22AM%2FA&store=R071",
    },
}

parser = argparse.ArgumentParser()
parser.add_argument(
    "-l",
    "--location",
    help="Location you want to check. Options: {}".format(STORES.keys()),
)

args = parser.parse_args()

if args.location is None:
    stores_to_check = [v for k, v in STORES.items()]
elif args.location not in STORES:
    print("Invalid store")
    exit(1)
else:
    stores_to_check = [STORES[args.location]]

print(
    "Checking {}...".format(
        ", ".join(store["name"] for store in stores_to_check)
    )
)

iteration_count = 0
last_date = {}

while True:
    print("\n*** Starting new check @ {}".format(datetime.datetime.now()))
    ok_responses = {}
    ko_responses = {}
    for selected_store in stores_to_check:
        try:
            resp = requests.get(selected_store["url"])
            if resp.status_code == 200:
                ok_responses[selected_store["name"]] = resp
            else:
                ko_responses[selected_store["name"]] = resp
        except Exception as e:
            ko_responses[selected_store["name"]] = e

    for store_name, resp in ok_responses.items():
        print("Successful response from {}".format(store_name))
        data = resp.json()
        pickup_search_quote = data["body"]["stores"][0]["partsAvailability"][
            "MWP22AM/A"
        ]["pickupSearchQuote"]
        split_data = pickup_search_quote.split("<br/>")
        if len(split_data) == 2:
            date = split_data[1]
            if (
                iteration_count > 0
                and store_name in last_date
                and last_date[store_name] != date
            ):
                success_msg = "The new date for {} is {}".format(
                    store_name, date
                )
                print("---> " + success_msg)
                client.messages.create(
                    to=TO_NUMBER, from_=FROM_NUMBER, body=success_msg
                )
                call_successful = False
                while not call_successful:
                    call = client.calls.create(
                        to=TO_NUMBER,
                        from_=FROM_NUMBER,
                        url=TWILIO_URL,
                        timeout=CALL_TIMEOUT,
                    )
                    time.sleep(CALL_TIMEOUT + GRACE_PERIOD)
                    call_status = client.calls(call.sid).fetch().status.upper()
                    if call_status == "COMPLETED":
                        call_successful = True
                        print("Call succesfully made. Resuming checks.")
                    else:
                        print(
                            "Call status '{}'. Attempting new call"
                            "...".format(call_status)
                        )
            elif iteration_count == 0:
                print("First iteration: {}".format(date))
            else:
                print("Date hasn't changed ({})".format(date))
            last_date[store_name] = date
        else:
            print(
                "The result couldn't be split by '<br/>': {}".format(
                    pickup_search_quote
                )
            )

    for store_name, resp in ko_responses.items():
        if isinstance(resp, requests.Response):
            print(
                "The request to {} returned status code {} and "
                "body:\n{}".format(store_name, resp.status_code, resp.text)
            )
        elif isinstance(resp, Exception):
            print(
                "The request to {} raised a '{}' exception with error "
                "number {} and message:\n{}".format(
                    store_name, type(resp).__name__, resp.errno, resp.message
                )
            )
        else:
            print(
                "The request returned an unknown object of type "
                "'{}'".format(type(resp).__name__)
            )

    iteration_count += 1

    time.sleep(RETRIAL_INTERVAL)

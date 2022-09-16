#!/usr/bin/env python3

import argparse
import configparser
import datetime

import requests

import colorprint
from utils import EmailConfig, send_email, wait_until_next_iteration


config = configparser.ConfigParser()
config.read("config.cfg")

SENDER_EMAIL_ADDRESS = config.get("general", "SENDER_EMAIL_ADDRESS")
SENDER_EMAIL_PASSWORD = config.get("general", "SENDER_EMAIL_PASSWORD")
SMTP_SERVER_ADDRESS = config.get("general", "SMTP_SERVER_ADDRESS")
SMTP_SERVER_PORT = config.getint("general", "SMTP_SERVER_PORT")
RECIPIENT_EMAIL_ADDRESS = config.get("general", "RECIPIENT_EMAIL_ADDRESS")
SEND_COPY_TO_SENDER = config.getboolean("general", "SEND_COPY_TO_SENDER")
RETRIAL_INTERVAL_IN_SECONDS = config.getint("general", "RETRIAL_INTERVAL_IN_SECONDS")
PRODUCT_CODE = config.get("general", "PRODUCT_CODE")
PRODUCT_URL = config.get("general", "PRODUCT_URL")

RECIPIENTS = [RECIPIENT_EMAIL_ADDRESS]
if SEND_COPY_TO_SENDER:
    RECIPIENTS.append(SENDER_EMAIL_ADDRESS)

email_config = EmailConfig(
    smtp_server_address=SMTP_SERVER_ADDRESS,
    smtp_server_port=SMTP_SERVER_PORT,
    sender_email_address=SENDER_EMAIL_ADDRESS,
    sender_email_password=SENDER_EMAIL_PASSWORD,
    recipients=RECIPIENTS,
)

PICKUP_AVAILABILITY_URL = "http://www.apple.com/shop/retail/pickup-message"
STORES = {
    "WACR": {"name": "Walnut Creek", "store_code": "R014"},
    "SFUS": {"name": "San Francisco Union Square", "store_code": "R075"},
    "SACR": {"name": "Sacramento Arden Fair", "store_code": "R070"},
    "ROSE": {"name": "Roseville", "store_code": "R298"},
    "4THS": {"name": "4th Street (Berkeley)", "store_code": "R414"},
    "BAYS": {"name": "Bay Street (Emeryville)", "store_code": "R057"},
    "STPL": {"name": "Stoneridge Mall (Pleasanton)", "store_code": "R101"},
    "CHEST": {"name": "Chestnut Street (SF)", "store_code": "R217"},
    "STSF": {"name": "Stonestown (SF)", "store_code": "R033"},
    "COMA": {"name": "Corte Madera", "store_code": "R071"},
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--location",
        help=f"Location you want to check",
        choices=STORES.keys(),
        required=False,
    )

    args = parser.parse_args()

    if args.location is None:
        stores_to_check = STORES.values()
    else:
        stores_to_check = [STORES[args.location]]

    print(f"Checking {', '.join(store['name'] for store in stores_to_check)}...")

    iteration_count = 0
    last_availability = {}
    for store in stores_to_check:
        last_availability[store["name"]] = {
            "pickupDisplay": None,
            "pickupSearchQuote": None,
        }

    while True:
        print(f"\n*** Starting new check @ {datetime.datetime.now()}")
        successful_responses = {}
        failed_responses = {}
        for store in stores_to_check:
            try:
                payload = {
                    "parts.0": PRODUCT_CODE,
                    "store": store["store_code"],
                }
                resp = requests.get(PICKUP_AVAILABILITY_URL, params=payload)
                resp.raise_for_status()
                successful_responses[store["name"]] = resp
            except Exception as e:
                failed_responses[store["name"]] = e

        for store_name, resp in successful_responses.items():
            data = resp.json()
            pickup_search_quote = data["body"]["stores"][0]["partsAvailability"][
                PRODUCT_CODE
            ]["pickupSearchQuote"]
            pickup_display = data["body"]["stores"][0]["partsAvailability"][
                PRODUCT_CODE
            ]["pickupDisplay"]

            print(f"{store_name} ({pickup_display}):\n  ", end="")

            changes_detected = (
                last_availability[store_name]["pickupDisplay"] != pickup_display
            ) or (
                last_availability[store_name]["pickupSearchQuote"]
                != pickup_search_quote
            )

            if pickup_display == "available":
                colorprint.success(pickup_search_quote)
                if changes_detected:
                    print(f"  Go buy one at {PRODUCT_URL}, you fool!")
                    print("  Sending email...")
                    try:
                        send_email(email_config, PRODUCT_URL)
                    except Exception as e:
                        print(f"  Could not send email: {str(e)}")
            else:
                colorprint.error(pickup_search_quote)

            last_availability[store_name]["pickupSearchQuote"] = pickup_search_quote
            last_availability[store_name]["pickupDisplay"] = pickup_display

        for store_name, resp in failed_responses.items():
            if isinstance(resp, requests.Response):
                print(
                    f"The request to {store_name} returned status code "
                    f"{resp.status_code} and body:\n{resp.text}"
                )
            elif isinstance(resp, Exception):
                print(
                    f"The request to {store_name} raised a '{type(resp).__name__}' "
                    f"exception with message:\n{str(resp)}"
                )
            else:
                print(
                    f"The request returned an unknown object of type "
                    f"'{type(resp).__name__}'"
                )

        iteration_count += 1
        wait_until_next_iteration(RETRIAL_INTERVAL_IN_SECONDS)

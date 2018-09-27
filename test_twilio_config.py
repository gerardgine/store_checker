#!/usr/bin/env python

from utils import check_twilio_version
check_twilio_version()

import ConfigParser
import time

from twilio.rest import Client


config = ConfigParser.ConfigParser()
config.read('config.cfg')

TO_NUMBER = config.get('Twilio', 'TO_NUMBER')
FROM_NUMBER = config.get('Twilio', 'FROM_NUMBER')
TWILIO_URL = config.get('Twilio', 'TWILIO_URL')
ACCOUNT_SID = config.get('Twilio', 'ACCOUNT_SID')
AUTH_TOKEN = config.get('Twilio', 'AUTH_TOKEN')
CALL_TIMEOUT = config.getint('Twilio', 'CALL_TIMEOUT')
GRACE_PERIOD = config.getint('Twilio', 'GRACE_PERIOD')
RETRIAL_INTERVAL = config.getint('Twilio', 'RETRIAL_INTERVAL')

client = Client(ACCOUNT_SID, AUTH_TOKEN)

message = "This is a test message."
client.messages.create(to=TO_NUMBER, from_=FROM_NUMBER, body=message)
print("Message successfully sent.")
call_successful = False
while not call_successful:
    call = client.calls.create(to=TO_NUMBER, from_=FROM_NUMBER, url=TWILIO_URL, timeout=CALL_TIMEOUT)
    print("Call started. Waiting for {} seconds...".format(CALL_TIMEOUT + GRACE_PERIOD))
    time.sleep(CALL_TIMEOUT + GRACE_PERIOD)
    call_status = client.calls(call.sid).fetch().status.upper()
    if call_status == "COMPLETED":
        call_successful = True
        print "Call succesfully made."
    else:
        print "Call status '{}'. Attempting new call...".format(call_status)

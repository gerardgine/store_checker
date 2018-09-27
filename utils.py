import sys

TWILIO_MINIMUM_VERSION = '6.17.0'
TWILIO_MINIMUM_MAJOR = 6
TWILIO_MINIMUM_MINOR = 17

def check_twilio_version():
    import twilio
    major, minor, _ = twilio.__version_info__
    major = int(major)
    minor = int(minor)
    if (major >= TWILIO_MINIMUM_MAJOR and minor >= TWILIO_MINIMUM_MINOR) \
           or (major > TWILIO_MINIMUM_MAJOR):
        print("Found Twilio version {}. OK.".format(twilio.__version__))
    else:
        print("Found Twilio version {}. Minimum version: {}. "
              "Exiting.".format(twilio.__version__, TWILIO_MINIMUM_VERSION))
        sys.exit(1)

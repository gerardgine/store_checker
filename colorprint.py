class bcolors:
    PINK = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def colorize(text, color):
    return "{}{}{}".format(color, text, bcolors.ENDC)


def debug(text, **kwargs):
    print(colorize(text, bcolors.BLUE), **kwargs)


def error(text, **kwargs):
    print(colorize(text, bcolors.RED), **kwargs)


def info(text, **kwargs):
    print(colorize(text, bcolors.BOLD), **kwargs)


def yellow_info(text, **kwargs):
    print(colorize(colorize(text, bcolors.YELLOW), bcolors.BOLD), **kwargs)


def success(text, **kwargs):
    print(colorize(text, bcolors.GREEN), **kwargs)


def warning(text, **kwargs):
    print(colorize(text, bcolors.YELLOW), **kwargs)


def normal(text, **kwargs):
    print(text, **kwargs)

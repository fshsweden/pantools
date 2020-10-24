import logging, sys, os

l = logging.DEBUG

if os.environ.get('LOG') == "INFO":
    print("Setting loglevel to INFO")
    l = logging.INFO
else:
    if os.environ.get('LOG') == "ERROR":
        print("Setting loglevel to ERROR")
        l = logging.ERROR
    else:
        if os.environ.get('LOG') == "WARNING":
            l = logging.WARNING
            print("Setting loglevel to WARNING")
        else:
            print("Setting loglevel to DEBUG")


logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d in function %(funcName)s] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=l
)

logger = logging.getLogger(__name__)

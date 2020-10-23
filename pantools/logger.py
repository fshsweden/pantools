import logging, sys, os

print("Konfigurerar Logging!")
logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d in function %(funcName)s] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)

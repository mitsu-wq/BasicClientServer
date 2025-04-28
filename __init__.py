import logging.config
from json import load
import os
from .BasicServer import BasicServer
from .BasicClient import BasicClient
from .MessageConverter import MessageConverter
from .MessageRegistry import MessageRegistry, MessageType

try:
    config_path = os.path.join(os.path.dirname(__file__), 'logging.json')
    with open(config_path, 'r') as f:
        logging.config.dictConfig(load(f))
except FileNotFoundError:
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger(__name__).warning("logging.json not found, using default logging")

__all__ = ['BasicServer', 'BasicClient', 'MessageConverter', 'MessageType', 'MessageRegistry']
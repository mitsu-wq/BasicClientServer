import socket
from typing import Optional
from logging import getLogger, DEBUG
from .MessageRegistry import MessageType, MessageRegistry
from .MessageConverter import MessageConverter

class BasicClient:
    def __init__(self):
        self.init_flag = False
        self.socket = None
        self.ip = None
        self.port = None
        self.registry = MessageRegistry()
        self._initialize_handlers()
        self.logger = getLogger("Client")
        self.logger.setLevel(DEBUG)
        self.logger.info("Client initialized")
    
    def _initialize_handlers(self):
        """Initializes handlers based on decorated methods."""
        for cls in self.__class__.__mro__[:-1]:  # Exclude object
            for name, method in cls.__dict__.items():
                if hasattr(method, '_message_handler'):
                    self.registry.register_handler(method.__get__(self, self.__class__))

    def open(self, ip: str, port: int) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))
            self.ip = ip
            self.port = port
            self.logger.info(f"Connection with {ip}:{port}")
            self.init_flag = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to open connection: {e}")
            return False

    def close(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
                return False
        self.init_flag = False
        self.socket = None
        self.ip = None
        self.port = None
        self.logger.info("Connection closed")
        return True

    def send_data(self, message_type: MessageType, data: bytes = b""):
        if not self.init_flag:
            self.logger.error("Not connected to server")
            return None
        try:
            msg = MessageConverter.encode_message(message_type, data)
            self.socket.send(msg)
            self.logger.info(f"Send data to {self.ip}:{self.port} - type: {message_type}, data: {data[:50]}")
            return self.get_message()
        except Exception as e:
            self.logger.error(f"Failed to send data: {e}")
            return None

    def get_message(self) -> Optional[object]:
        if not self.init_flag:
            return None
        try:
            raw_data = self.socket.recv(MessageConverter.HEADER_SIZE + MessageConverter.MAX_LENGTH)
            if not raw_data:
                self.logger.info("Server disconnected")
                return None
            msg_type, data = MessageConverter.decode_message(raw_data)
            if msg_type is None:
                self.logger.warning("Invalid message received")
                return None
            self.logger.info(f"Received data from {self.ip}:{self.port} - type: {msg_type}, data: {data[:50]}")
            return self.registry.process(msg_type, data)
        except socket.timeout:
            self.logger.warning("Timeout waiting for message")
            return None
        except Exception as e:
            self.logger.error(f"Error getting message: {e}")
            return None
    
    @MessageRegistry.handler("CHECK")
    def _check(self, data: bytes) -> bool:
        if not self.init_flag:
            return None
        return data
    
    @MessageRegistry.handler("ERROR")
    def _error(self, data: bytes):
        self.logger.error(f"Error: {data}")
        return None
import socket
from typing import Callable, Optional
from logging import getLogger, DEBUG
from BasicClientServer.MessageUtils import MessageConverter, MessageType
from BasicClientServer.MessageHandler import MessageHandler

class BasicClient:
    def __init__(self):
        self.init_flag = False
        self.socket = None
        self.ip = None
        self.port = None
        self.logger = getLogger("Client")
        self.logger.setLevel(DEBUG)
        self.message_handler = MessageHandler(owner=self, is_server=False)
        self.logger.info("Client initialized")

    def open(self, port: int, ip: str = None, subnet_port_checker=None) -> bool:
        try:
            if subnet_port_checker is not None:
                ips = subnet_port_checker.get_open_addresses(port)
                ip = ips[0] if len(ips) != 0 else None
            if ip is None:
                self.logger.error("No available ips to connect")
                return False
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

    def get_message(self) -> Optional[dict]:
        if not self.init_flag:
            return None
        try:
            header = self.socket.recv(MessageConverter.HEADER_SIZE)
            if not header:
                self.logger.info("Server disconnected")
                return None
            raw_data = header + self.socket.recv(MessageConverter.MAX_LENGTH) if len(header) == MessageConverter.HEADER_SIZE else b""
            msg_type, data = MessageConverter.decode_message(raw_data)
            if msg_type is None:
                self.logger.warning("Invalid message received")
                return None
            self.logger.info(f"Received data from {self.ip}:{self.port} - type: {msg_type}, data: {data[:50]}")
            return self.message_handler.process_message(msg_type, data)
        except socket.timeout:
            self.logger.warning("Timeout waiting for message")
            return None
        except Exception as e:
            self.logger.error(f"Error getting message: {e}")
            return None

    def register_message_handler(self, msg_type: MessageType, handler: Callable[[bytes], dict]):
        """
        Register a message handler for a specific message type.
        
        Args:
            msg_type: The message type to handle.
            handler: Function that takes data (bytes) and returns a dict.
        """
        self.message_handler.register_handler(msg_type, handler, is_server=False)
    
    def check_connection(self):
        if not self.init_flag:
            return False
        try:
            response = self.send_data(MessageType.CHECK)
            return response is not None and response["type"] == MessageType.CHECK
        except Exception as e:
            self.logger.error(f"Error checking connection: {e}")
            return False
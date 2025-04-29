import socket
from typing import Optional
from .NetworkComponent import NetworkComponent
from .MessageRegistry import MessageType, MessageRegistry
from .MessageConverter import MessageConverter
from .NetworkConfig import NetworkConfig

class BasicClient(NetworkComponent):
    """Client implementation for network communication."""
    
    def __init__(self):
        """Initialize client with empty connection state."""
        super().__init__()
        self.init_flag = False
        self.socket = None
        self.ip = None
        self.port = None

    def open(self, ip: str, port: int) -> bool:
        """Connect to server at specified IP and port. Returns True if successful."""
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
        """Close connection to server. Returns True if successful."""
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
        """Send data to server and wait for response. Returns response or None on error."""
        if not self.init_flag:
            self.logger.error("Not connected to server")
            return None
        if self._send_message(self.socket, message_type, data):
            return self.get_message()
        return None

    def get_message(self) -> Optional[object]:
        """Receive and process next message from server. Returns None on error or timeout."""
        if not self.init_flag:
            return None
        try:
            raw_data = self.socket.recv(NetworkConfig.HEADER_SIZE + NetworkConfig.MAX_LENGTH)
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
    def _check(self, data: bytes):
        """Handle CHECK message type. Returns data if connected."""
        if not self.init_flag:
            return None
        return data
    
    @MessageRegistry.handler("ERROR")
    def _error(self, data: bytes) -> None:
        """Handle ERROR message type by logging the error."""
        self._handle_error(data)
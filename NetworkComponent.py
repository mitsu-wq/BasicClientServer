import socket
from logging import DEBUG, getLogger
from .MessageRegistry import MessageRegistry, MessageType
from .MessageConverter import MessageConverter


class NetworkComponent:
    """Base class for network communication components (client and server)."""
    
    def __init__(self):
        """Initialize the network component with registry and logger."""
        self.registry = MessageRegistry()
        self.logger = getLogger(self.__class__.__name__)
        self.logger.setLevel(DEBUG)
        self._initialize_handlers()
        self.logger.info(f"{self.__class__.__name__} initialized")

    def _initialize_handlers(self):
        """Register all message handlers decorated with @MessageRegistry.handler."""
        for cls in self.__class__.__mro__[:-1]:  # Exclude object
            for name, method in cls.__dict__.items():
                if hasattr(method, '_message_handler'):
                    self.registry.register_handler(method.__get__(self, self.__class__))
    
    def _handle_error(self, data: bytes) -> None:
        """Log error messages received from the network."""
        self.logger.error(f"Error: {data}")
    
    def _send_message(self, sock: socket.socket, message_type: MessageType, data: bytes = b"") -> bool:
        """Send a message through the socket. Returns True if successful."""
        try:
            msg = MessageConverter.encode_message(message_type, data)
            sock.send(msg)
            self.logger.info(f"Sent message - type: {message_type}, data: {data[:50]}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
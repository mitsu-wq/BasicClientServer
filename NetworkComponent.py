import socket
from logging import DEBUG, getLogger
from .MessageRegistry import MessageRegistry, MessageType
from .MessageConverter import MessageConverter


class NetworkComponent:
    def __init__(self):
        self.registry = MessageRegistry()
        self.logger = getLogger(self.__class__.__name__)
        self.logger.setLevel(DEBUG)
        self._initialize_handlers()
        self.logger.info(f"{self.__class__.__name__} initialized")

    def _initialize_handlers(self):
        """Initializes handlers based on decorated methods."""
        for cls in self.__class__.__mro__[:-1]:  # Exclude object
            for name, method in cls.__dict__.items():
                if hasattr(method, '_message_handler'):
                    self.registry.register_handler(method.__get__(self, self.__class__))
    
    def _handle_error(self, data: bytes) -> None:
        """Handles error messages by logging them."""
        self.logger.error(f"Error: {data}")
    
    def _send_message(self, sock: socket.socket, message_type: MessageType, data: bytes = b"") -> bool:
        """Sends a message through the given socket."""
        try:
            msg = MessageConverter.encode_message(message_type, data)
            sock.send(msg)
            self.logger.info(f"Sent message - type: {message_type}, data: {data[:50]}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
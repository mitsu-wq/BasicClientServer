from typing import Callable, Optional, Union, Dict
from logging import getLogger, DEBUG
from BasicClientServer.MessageUtils import MessageConverter, MessageType

class MessageHandler:
    """
    Manages message handlers for both server and client.
    Server handlers: bytes -> bytes
    Client handlers: bytes -> dict
    """
    def __init__(self, owner: Optional[object] = None, is_server: bool = False):
        self.logger = getLogger("MessageHandler")
        self.logger.setLevel(DEBUG)
        self.is_server = is_server
        self.server_handlers: Dict[MessageType, Callable[[bytes], bytes]] = {
            MessageType.CHECK: self.handle_check_message_server,
            MessageType.DATA: self.handle_data_message_server,
            MessageType.ERROR: self.handle_error_message_server,
        }
        self.client_handlers: Dict[MessageType, Callable[[bytes], dict]] = {
            MessageType.CHECK: self.handle_check_message_client,
            MessageType.DATA: self.handle_data_message_client,
            MessageType.ERROR: self.handle_error_message_client,
        }
        self.logger.info("MessageHandler initialized")
        # Автоматическая регистрация обработчиков с декоратором @message_handler
        if owner:
            self._auto_register_handlers(owner)

    def _auto_register_handlers(self, owner: object):
        """
        Automatically register methods decorated with @message_handler.
        
        Args:
            owner: The object (e.g., BasicServer or BasicClient instance) to scan for handlers.
        """
        for attr_name in dir(owner):
            method = getattr(owner, attr_name)
            if callable(method) and getattr(method, '_message_handler', False):
                msg_type = method._msg_type
                if self.is_server:
                    self.register_handler(msg_type, method, is_server=True)
                else:
                    self.register_handler(msg_type, method, is_server=False)
                self.logger.info(f"Auto-registered handler {attr_name} for {msg_type}")

    def register_handler(self, msg_type: MessageType, handler: Callable, is_server: bool = False):
        """
        Register a handler for a specific message type.
        
        Args:
            msg_type: The message type to handle.
            handler: Function (bytes -> bytes for server, bytes -> dict for client).
            is_server: Whether this is a server handler.
        """
        if is_server:
            self.server_handlers[msg_type] = handler
        else:
            self.client_handlers[msg_type] = handler
        self.logger.info(f"Registered {'server' if is_server else 'client'} handler for {msg_type}")

    def process_message(self, msg_type: MessageType, data: bytes) -> Union[bytes, Optional[dict]]:
        """
        Process a message using the registered handler.
        
        Args:
            msg_type: The message type.
            data: The message data.
        
        Returns:
            Bytes (server) or dict (client) response, or ERROR message/None on failure.
        """
        handlers = self.server_handlers if self.is_server else self.client_handlers
        handler = handlers.get(msg_type)
        if handler:
            try:
                return handler(data)
            except Exception as e:
                self.logger.error(f"Error in handler for {msg_type}: {e}")
                return MessageConverter.encode_message(MessageType.ERROR) if self.is_server else None
        self.logger.warning(f"No handler for message type: {msg_type}")
        return MessageConverter.encode_message(MessageType.ERROR) if self.is_server else None

    def handle_check_message_server(self, data: bytes) -> bytes:
        self.logger.info("Received CHECK message (server)")
        return MessageConverter.encode_message(MessageType.CHECK)

    def handle_data_message_server(self, data: bytes) -> bytes:
        # Пример интерпретации: первые 4 байта как int, остальное как строка
        if len(data) >= 4:
            number = int.from_bytes(data[:4], 'big')
            text = data[4:].decode('utf-8', errors='ignore')
            self.logger.info(f"Received DATA (server): number={number}, text={text}")
            # Ответ: инкремент числа + эхо строки
            response = (number + 1).to_bytes(4, 'big') + data[4:]
            return MessageConverter.encode_message(MessageType.DATA, response)
        self.logger.error("Invalid DATA format (server)")
        return MessageConverter.encode_message(MessageType.ERROR)

    def handle_error_message_server(self, data: bytes) -> bytes:
        self.logger.warning("Received ERROR message (server)")
        return MessageConverter.encode_message(MessageType.ERROR)

    def handle_check_message_client(self, data: bytes) -> dict:
        self.logger.info("Received CHECK message (client)")
        return {"type": MessageType.CHECK, "data": data}

    def handle_data_message_client(self, data: bytes) -> dict:
        # Пример интерпретации: первые 4 байта как int, остальное как строка
        if len(data) >= 4:
            number = int.from_bytes(data[:4], 'big')
            text = data[4:].decode('utf-8', errors='ignore')
            self.logger.info(f"Received DATA (client): number={number}, text={text}")
            return {"type": MessageType.DATA, "number": number, "text": text}
        self.logger.error("Invalid DATA format (client)")
        return {"type": MessageType.ERROR, "data": b""}

    def handle_error_message_client(self, data: bytes) -> dict:
        self.logger.warning("Received ERROR message (client)")
        return {"type": MessageType.ERROR, "data": data}
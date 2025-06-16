import asyncio
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
        self.reader = None
        self.writer = None
        self.ip = None
        self.port = None

    async def open(self, ip: str, port: int) -> bool:
        """Connect to server at specified IP and port. Returns True if successful."""
        try:
            self.reader, self.writer = await asyncio.open_connection(ip, port)
            self.ip = ip
            self.port = port
            self.logger.info(f"Connection with {ip}:{port}")
            self.init_flag = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to open connection: {e}")
            return False

    async def close(self):
        """Close connection to server. Returns True if successful."""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
                return False
        self.init_flag = False
        self.reader = None
        self.writer = None
        self.ip = None
        self.port = None
        self.logger.info("Connection closed")
        return True

    async def send_data(self, message_type: MessageType, data: bytes = b""):
        """Send data to server and wait for response. Returns response or None on error."""
        if not self.init_flag:
            self.logger.error("Not connected to server")
            return None
        if await self._send_message(self.writer, message_type, data):
            return await self.get_message()
        return None

    async def get_message(self) -> Optional[object]:
        """Receive and process next message from server. Returns None on error or timeout."""
        if not self.init_flag:
            return None
        try:
            raw_data = await asyncio.wait_for(
                self.reader.read(NetworkConfig.HEADER_SIZE + NetworkConfig.MAX_LENGTH), timeout=5.0
            )
            if not raw_data:
                self.logger.info("Server disconnected")
                return None
            msg_type, data = MessageConverter.decode_message(raw_data)
            if msg_type is None:
                self.logger.warning("Invalid message received")
                return None
            self.logger.info(f"Received data from {self.ip}:{self.port} - type: {msg_type}, data: {data[:50]}")
            return await self.registry.process(msg_type, data)
        except asyncio.TimeoutError:
            self.logger.warning("Timeout waiting for message")
            return None
        except Exception as e:
            self.logger.error(f"Error getting message: {e}")
            return None
    
    @MessageRegistry.handler("CHECK")
    async def _check(self, data: bytes):
        """Handle CHECK message type. Returns data if connected."""
        if not self.init_flag:
            return None
        return data
    
    @MessageRegistry.handler("ERROR")
    async def _error(self, data: bytes) -> None:
        """Handle ERROR message type by logging the error."""
        self._handle_error(data)
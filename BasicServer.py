import asyncio
from concurrent.futures import ThreadPoolExecutor
from .MessageRegistry import MessageRegistry, MessageType
from .MessageConverter import MessageConverter
from .NetworkComponent import NetworkComponent
from .NetworkConfig import NetworkConfig

class BasicServer(NetworkComponent):
    """Server implementation for handling multiple client connections."""
    
    def __init__(self):
        """Initialize server with empty connection state."""
        super().__init__()
        self.init_flag = False
        self.server = None
        self.active_tasks = []
        self.loop = asyncio.get_event_loop()

    async def open(self, port: int, ip: str = '0.0.0.0', max_clients: int = 1):
        """Start server on specified port and IP. Returns True if successful."""
        try:
            self.server = await asyncio.start_server(
                self.client_read_task,
                ip,
                port,
                limit=NetworkConfig.MAX_LENGTH + NetworkConfig.HEADER_SIZE
            )
            self.init_flag = True
            self.logger.info(f"Server started on {ip}:{port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False

    async def close(self):
        """Stop server and close all client connections."""
        try:
            if self.init_flag:
                self.server.close()
                await self.server.wait_closed()
                for task in self.active_tasks:
                    task.cancel()
                await asyncio.gather(*self.active_tasks, return_exceptions=True)
                self.active_tasks = []
                self.init_flag = False
                self.logger.info("Server closed")
        except Exception as e:
            self.logger.error(f"Error closing server: {e}")
        finally:
            self.server = None

    async def client_read_task(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle individual client communication."""
        addr = writer.get_extra_info("peername")
        self.logger.info(f"Connection from {addr}")
        task = asyncio.current_task()
        self.active_tasks.append(task)
        try:
            while True:
                try:
                    raw_data = await asyncio.wait_for(
                        reader.read(NetworkConfig.HEADER_SIZE + NetworkConfig.MAX_LENGTH),
                        timeout=5.0
                    )
                    if not raw_data:
                        self.logger.info(f"Client {addr} disconnected.")
                        break
                    self.logger.debug(f"Received data: {raw_data}")
                    msg_type, data = MessageConverter.decode_message(raw_data)
                    if msg_type is None:
                        self.logger.warning(f"Invalid message from {addr}")
                        await self._send_message(writer, MessageType.ERROR, b"Invalid message")
                        break
                    self.logger.info(f"Message from {addr} - type: {msg_type}, data: {data[:50]}")
                    response = await self.registry.process(msg_type, data)
                    self.logger.debug(f"Response: {response}")
                    if response is not None:
                        await self._send_message(writer, msg_type, response)
                    else:
                        await self._send_message(writer, MessageType.ERROR, b"Invalid message")
                except asyncio.TimeoutError:
                    message = "Timeout waiting for message"
                    self.logger.warning(f"{message} from {addr}")
                    await self._send_message(writer, MessageType.ERROR, message.encode())
                    break
                except Exception as e:
                    message = "Failed processing connection"
                    self.logger.error(f"{message} {addr}: {e}")
                    await self._send_message(writer, MessageType.ERROR, f"{message}: {e}".encode())
                    break
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            self.active_tasks.remove(task)
    
    @MessageRegistry.handler("CHECK")
    async def _check(self, data: bytes):
        """Handle CHECK message type by echoing back the data."""
        return data
    
    @MessageRegistry.handler("ERROR")
    async def _error(self, data: bytes):
        """Handle ERROR message type by logging the error."""
        self._handle_error(data)
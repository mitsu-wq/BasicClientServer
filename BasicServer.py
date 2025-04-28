import threading
import socket
from concurrent.futures import ThreadPoolExecutor
from .MessageRegistry import MessageRegistry, MessageType
from .MessageConverter import MessageConverter
from .NetworkComponent import NetworkComponent
from .NetworkConfig import NetworkConfig

class BasicServer(NetworkComponent):
    def __init__(self):
        super().__init__()
        self.init_flag = False
        self.socket = None
        self.stop_clients_thread_flag = threading.Event()
        self.listen_clients_multithread = None
        self.clients_thread = None
        self.active_futures = []

    def open(self, port: int, ip: str = '0.0.0.0', max_clients: int = 1):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((ip, port))
            self.socket.listen(max_clients)
            self.stop_clients_thread_flag.clear()
            self.listen_clients_multithread = ThreadPoolExecutor(max_workers=max_clients)
            self.clients_thread = threading.Thread(target=self.get_clients_thread)
            self.clients_thread.daemon = True
            self.clients_thread.start()
            self.init_flag = True
            self.logger.info(f"Server started on {ip}:{port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            return False

    def close(self):
        try:
            if self.init_flag:
                self.stop_clients_thread_flag.set()
                if self.socket:
                    self.socket.close()
                if self.listen_clients_multithread:
                    self.logger.info(f"Active futures before shutdown: {len([f for f in self.active_futures if not f.done()])}")
                    self.listen_clients_multithread.shutdown(wait=True)
                if self.clients_thread:
                    self.clients_thread.join()
                self.init_flag = False
                self.logger.info("Server closed")
        except Exception as e:
            self.logger.error(f"Error closing server: {e}")
        finally:
            self.socket = None
            self.listen_clients_multithread = None
            self.clients_thread = None
            self.active_futures = []

    def get_clients_thread(self):
        while not self.stop_clients_thread_flag.is_set():
            try:
                self.socket.settimeout(1.0)
                client, addr = self.socket.accept()
                self.logger.info(f"Connection from {addr}")
                future = self.listen_clients_multithread.submit(self.client_read_thread, client, addr)
                self.active_futures.append(future)
                self.logger.debug(f"Submitted task for {addr}, active futures: {len([f for f in self.active_futures if not f.done()])}")
            except socket.timeout:
                continue
            except Exception as e:
                if not self.stop_clients_thread_flag.is_set():
                    self.logger.error(f"Error accepting connection: {e}")
                break

    def client_read_thread(self, client, addr):
        try:
            while not self.stop_clients_thread_flag.is_set():
                try:
                    raw_data = client.recv(NetworkConfig.HEADER_SIZE + NetworkConfig.MAX_LENGTH)
                    if not raw_data:
                        self.logger.info(f"Client {addr} disconnected")
                        break
                    self.logger.debug(f"Received data: {raw_data}")
                    msg_type, data = MessageConverter.decode_message(raw_data)
                    if msg_type is None:
                        self.logger.warning(f"Invalid message from {addr}")
                        self._send_message(client, MessageType.ERROR)
                        break
                    self.logger.info(f"Message from {addr} - type: {msg_type}, data: {data[:50]}")
                    response = self.registry.process(msg_type, data)
                    self.logger.debug(f"Response: {response}")
                    if response is not None:
                        self._send_message(client, msg_type, response)
                    else:
                        self._send_message(client, MessageType.ERROR)
                except socket.timeout:
                    self.logger.warning(f"Timeout waiting for message from {addr}")
                    self._send_message(client, MessageType.ERROR)
                    break
                except Exception as e:
                    self.logger.error(f"Failed processing connection {addr}: {e}")
                    self._send_message(client, MessageType.ERROR)
                    break
        finally:
            try:
                client.close()
            except:
                pass
    
    @MessageRegistry.handler("CHECK")
    def _check(self, data: bytes):
        return data
    
    @MessageRegistry.handler("ERROR")
    def _error(self, data: bytes):
        self._handle_error(data)
import threading
import socket
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger, DEBUG
from typing import Callable
from BasicClientServer.MessageUtils import MessageConverter, MessageType
from BasicClientServer.MessageHandler import MessageHandler

class BasicServer:
    def __init__(self):
        self.init_flag = False
        self.socket = None
        self.stop_clients_thread_flag = threading.Event()
        self.listen_clients_multithread = None
        self.clients_thread = None
        self.active_futures = []
        self.logger = getLogger("Server")
        self.logger.setLevel(DEBUG)
        self.message_handler = MessageHandler(owner=self, is_server=True)
        self.logger.info("Server initialized")
        
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
                    header = client.recv(MessageConverter.HEADER_SIZE)
                    if not header:
                        self.logger.info(f"Client {addr} disconnected")
                        break
                    raw_data = header + client.recv(MessageConverter.MAX_LENGTH) if len(header) == MessageConverter.HEADER_SIZE else b""
                    msg_type, data = MessageConverter.decode_message(raw_data)
                    if msg_type is None:
                        self.logger.warning(f"Invalid message from {addr}")
                        client.send(MessageConverter.encode_message(MessageType.ERROR))
                        break
                    self.logger.info(f"Message from {addr} - type: {msg_type}, data: {data[:50]}")
                    response = self.message_handler.process_message(msg_type, data)
                    client.send(response)
                except socket.timeout:
                    self.logger.warning(f"Timeout waiting for message from {addr}")
                    break
                except Exception as e:
                    self.logger.error(f"Failed processing connection {addr}: {e}")
                    break
        finally:
            try:
                client.close()
            except:
                pass

    def register_message_handler(self, msg_type: MessageType, handler: Callable[[bytes], bytes]):
        """
        Register a message handler for a specific message type.
        
        Args:
            msg_type: The message type to handle.
            handler: Function that takes data (bytes) and returns response (bytes).
        """
        self.message_handler.register_handler(msg_type, handler, is_server=True)
from .NetworkConfig import NetworkConfig
from .MessageRegistry import MessageType
from typing import Optional, Tuple

class MessageConverter:
    """Static utility for encoding and decoding messages."""
    @staticmethod
    def encode_message(msg_type: MessageType, data: bytes = b"") -> bytes:
        if len(data) > NetworkConfig.MAX_LENGTH:
            raise ValueError(f"Data length {len(data)} exceeds maximum of {NetworkConfig.MAX_LENGTH} bytes")
        return msg_type.value.to_bytes(1, 'big') + data

    @staticmethod
    def decode_message(raw_data: bytes) -> Tuple[Optional[MessageType], bytes]:
        if not raw_data or len(raw_data) < NetworkConfig.HEADER_SIZE:
            return None, b""
        try:
            msg_type = MessageType.get_by_value(int.from_bytes(raw_data[0:NetworkConfig.HEADER_SIZE], 'big'))
            if msg_type is None:
                return None, b""
            if len(raw_data) > NetworkConfig.HEADER_SIZE:
                data = raw_data[NetworkConfig.HEADER_SIZE:]
            else:
                data = b""
            return msg_type, data
        except (ValueError, IndexError):
            return None, b""
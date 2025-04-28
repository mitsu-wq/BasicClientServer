from typing import Optional, Tuple
from .MessageRegistry import MessageType

class MessageConverter:
    """Static utility for encoding and decoding messages."""
    HEADER_SIZE = 1
    MAX_LENGTH = 255

    @staticmethod
    def encode_message(msg_type: MessageType, data: bytes = b"") -> bytes:
        if len(data) > MessageConverter.MAX_LENGTH:
            raise ValueError(f"Data length {len(data)} exceeds maximum of {MessageConverter.MAX_LENGTH} bytes")
        return msg_type.value.to_bytes(1, 'big') + data

    @staticmethod
    def decode_message(raw_data: bytes) -> Tuple[Optional[MessageType], bytes]:
        if not raw_data or len(raw_data) < MessageConverter.HEADER_SIZE:
            return None, b""
        try:
            msg_type = MessageType.get_by_value(int.from_bytes(raw_data[0:1], 'big'))
            if msg_type is None:
                return None, b""
            if len(raw_data) > MessageConverter.HEADER_SIZE:
                data = raw_data[1:]
            else:
                data = b""
            return msg_type, data
        except (ValueError, IndexError):
            return None, b""
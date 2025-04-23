from enum import IntEnum
from typing import Optional, Tuple, Union
from functools import wraps

class MessageType(IntEnum):
    CHECK = 0
    DATA = 1
    ERROR = 2

    @classmethod
    def register(cls, name: str, value: int) -> 'MessageType':
        """
        Register a new MessageType dynamically.
        
        Args:
            name: Name of the new message type (e.g., 'AUTH').
            value: Unique integer value for the message type.
        
        Returns:
            The newly created MessageType member.
        
        Raises:
            ValueError: If value is already in use or invalid.
        """
        if value in cls._value2member_map_:
            raise ValueError(f"MessageType value {value} is already in use")
        if not (0 <= value <= 255):
            raise ValueError("MessageType value must be between 0 and 255")
        new_member = cls._create_pseudo_member_(value)
        cls._value2member_map_[value] = new_member
        setattr(cls, name, new_member)
        new_member._name_ = name
        return new_member

def message_handler(msg_type: Union[str, MessageType], type_value: Optional[int] = None):
    """
    Decorator to mark a function as a message handler for a specific MessageType.
    
    Args:
        msg_type: MessageType instance or string name (e.g., 'COUNTER').
        type_value: Optional integer value for new MessageType if string is provided.
    
    Returns:
        Decorator function that adds MessageType metadata to the handler.
    """
    def decorator(func):
        if isinstance(msg_type, str):
            try:
                actual_msg_type = MessageType[msg_type]
            except KeyError:
                if type_value is None:
                    raise ValueError(f"MessageType '{msg_type}' does not exist and no type_value provided")
                actual_msg_type = MessageType.register(msg_type, type_value)
        else:
            actual_msg_type = msg_type
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper._message_handler = True
        wrapper._msg_type = actual_msg_type
        return wrapper
    return decorator

class MessageConverter:
    """
    Static utility for encoding and decoding messages.
    Message format: [type (1 byte)] [data length (1 byte)] [data (0-255 bytes)]
    """
    HEADER_SIZE = 2  # 1 byte for type + 1 byte for data length
    MAX_LENGTH = 255  # Maximum data length

    @staticmethod
    def encode_message(msg_type: MessageType, data: bytes = b"") -> bytes:
        """
        Encode a message into bytes: type (1 byte) + data length (1 byte) + data.
        
        Args:
            msg_type: The type of the message.
            data: Optional data payload (up to 255 bytes).
        
        Returns:
            Bytes representing the full message.
        
        Raises:
            ValueError: If data length exceeds 255 bytes.
        """
        if len(data) > MessageConverter.MAX_LENGTH:
            raise ValueError(f"Data length {len(data)} exceeds maximum of {MessageConverter.MAX_LENGTH} bytes")
        return msg_type.value.to_bytes(1, 'big') + len(data).to_bytes(1, 'big') + data

    @staticmethod
    def decode_message(raw_data: bytes) -> Tuple[Optional[MessageType], bytes]:
        """
        Decode a message from bytes into type and data.
        
        Args:
            raw_data: Raw bytes received.
        
        Returns:
            Tuple of (MessageType or None, data bytes). Returns (None, b"") on error.
        """
        if not raw_data or len(raw_data) < MessageConverter.HEADER_SIZE:
            return None, b""
        try:
            msg_type = MessageType(int.from_bytes(raw_data[0:1], 'big'))
            data_len = int.from_bytes(raw_data[1:2], 'big')
            if data_len > MessageConverter.MAX_LENGTH or len(raw_data) < MessageConverter.HEADER_SIZE + data_len:
                return None, b""
            data = raw_data[MessageConverter.HEADER_SIZE:MessageConverter.HEADER_SIZE + data_len]
            return msg_type, data
        except (ValueError, IndexError):
            return None, b""
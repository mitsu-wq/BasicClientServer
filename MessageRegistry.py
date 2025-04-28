from typing import Union, Callable
from functools import wraps
from threading import Lock


class MessageType:
    """Class that emulates Enum for dynamically adding message types."""
    _members: dict = {}
    _lock = Lock()

    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"<MessageType.{self.name}: {self.value}>"

    @classmethod
    def register(cls, name: str) -> 'MessageType':
        """Registers a new message type or returns an existing one."""
        with cls._lock:
            if not name.isidentifier():
                raise ValueError(f"'{name}' is not a valid identifier")
            if name in cls._members:
                return cls._members[name]
            value = len(cls._members)
            message_type = MessageType(name, value)
            cls._members[name] = message_type
            setattr(cls, name, message_type)
            return message_type

    @classmethod
    def get(cls, name: str) -> 'MessageType':
        """Gets the message type by name."""
        return cls._members.get(name)
    
    @classmethod
    def get_by_value(cls, value: int) -> 'MessageType':
        """Gets the message type by value."""
        return next((message_type for message_type in cls._members.values() if message_type.value == value), None)

    @classmethod
    def members(cls) -> dict:
        """Returns all registered message types."""
        return cls._members.copy()


class MessageRegistry:
    """Class for managing message handlers."""
    def __init__(self):
        self.handlers: dict[MessageType, Callable] = {}

    @staticmethod
    def handler(name: Union[str]):
        """Decorator for marking message handlers."""
        def decorator(func: Callable) -> Callable:
            MessageType.register(name)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            wrapper._message_handler = True
            wrapper._msg_type = name
            return wrapper
        return decorator

    def register_handler(self, func: Callable):
        """Registers a handler for a function marked with a decorator."""
        if hasattr(func, '_message_handler') and hasattr(func, '_msg_type'):
            message_type = MessageType.get(func._msg_type)
            if message_type:
                self.handlers[message_type] = func

    def process(self, message_type: Union[str, MessageType], *args, **kwargs):
        """Invokes the handler for the specified message type."""
        if isinstance(message_type, str):
            message_type = MessageType.get(message_type)
        if not message_type:
            raise ValueError(f"Unknown message type: {message_type}")
        handler = self.handlers.get(message_type)
        if not handler:
            raise ValueError(f"No handler for message type: {message_type}")
        return handler(*args, **kwargs)

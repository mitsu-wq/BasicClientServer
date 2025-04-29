# Basic Client-Server Network Communication Framework

A lightweight Python framework for building client-server applications with custom message types and handlers.

## Features

- Custom message type registration and handling
- Automatic handler discovery through decorators
- Built-in error handling and logging
- Extensible architecture for both client and server implementations
- Type-safe message handling
- Thread-safe message type registration
- Configurable logging

## Installation

Clone the repository:
```bash
git clone https://github.com/mitsu-wq/BasicClientServer
cd BasicClientServer
```

## Project Structure

```
BasicClientServer/
├── NetworkComponent.py    # Base class for network communication
├── MessageRegistry.py     # Message type registration and handling
├── MessageConverter.py    # Message encoding/decoding
├── BasicServer.py        # Server implementation
├── BasicClient.py        # Client implementation
├── NetworkConfig.py      # Network configuration constants
└── logging.json          # Logging configuration
```

## Basic Usage

### Starting a Server

```python
from BasicClientServer import BasicServer, MessageRegistry, MessageType

class MyServer(BasicServer):
    @MessageRegistry.handler("CUSTOM")
    def handle_custom_message(self, data: bytes):
        self.logger.info(f"Received custom message: {data}")
        return b"Response data"

server = MyServer()
server.open(port=8080)  # Start server on port 8080
input()
```

### Creating a Client

```python
from BasicClientServer import BasicClient, MessageRegistry, MessageType

class MyClient(BasicClient):
    @MessageRegistry.handler("CUSTOM")
    def handle_custom_message(self, data: bytes):
        self.logger.info(f"Received response: {data}")

client = MyClient()
client.open("localhost", 8080)  # Connect to server
client.send_data(MessageType.CUSTOM, b"Hello, server!")
```

## Message Types

The framework uses a dynamic message type system. Message types are registered using the `@MessageRegistry.handler` decorator:

```python
@MessageRegistry.handler("CUSTOM")
def handle_new_type(self, data: bytes):
    # Handle the new message type
    return b"Response data"
```

Built-in message types:
- `CHECK`: For connection verification
- `ERROR`: For error messages

## Error Handling

The framework provides built-in error handling through the `_handle_error` method. You can override this method in your implementation:

```python
def _handle_error(self, data: bytes) -> None:
    # Custom error handling logic
    self.logger.error(f"Custom error handling: {data}")
```

## Logging

The framework uses Python's built-in logging module with configuration from `logging.json`. You can customize the logging configuration:

```json
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler"
        }
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": true
        }
    }
}
```

## Extending the Framework

### Adding New Message Types and creating Custom Message Handlers

1. Define a new message type using the decorator in server and client:
```python
@MessageRegistry.handler("CUSTOM")
def handle_new_type(self, data: bytes):
    # Process the message
    return b"Response data"
```

2. The handlers will be automatically registered and called when messages of that type are received.

3. Use the new message type in your client/server code:
```python
client.send_data(MessageType.CUSTOM, b"Data")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
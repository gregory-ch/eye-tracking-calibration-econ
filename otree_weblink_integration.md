# Integrating oTree with WebLink for Eye Tracking

## Architecture Overview

```
┌───────────────┐   HTTP/WebSocket   ┌───────────────┐   TCP/UDP Socket   ┌───────────────┐
│  Web Browser  │ ←────────────────→ │  oTree Server │ ←────────────────→ │  WebLink/Host │
└───────────────┘                    └───────────────┘                    └───────────────┘
    Participant                         Experiment                         Eye Tracking
```

This document describes how to integrate oTree experiments with SR Research's WebLink software for eye tracking studies.

## 1. Communication Principles

### 1.1. Data Flow

1. **Browser → oTree**: JavaScript events via WebSocket (`liveSend`)
2. **oTree → WebLink**: TCP/UDP socket communication
3. **WebLink → Host PC**: Internal communication for EDF file recording

### 1.2. Technical Details

- **Protocol Options**: TCP (guaranteed delivery) or UDP (faster, no acknowledgment)
- **Default Ports**: 50700 (TCP) or 50600 (UDP)
- **Message Formats**: Plain text or commands with format `eyecmd ... endcmd`

## 2. Required Libraries

### 2.1. Python Standard Libraries

```python
import socket       # For network communication
import logging      # For error logging
import time         # For timing operations
```

### 2.2. oTree Libraries

```python
from otree.api import *  # Core oTree functionality
```

## 3. Socket Communication Class Structure

The core of the integration is a socket communication class to handle connections with WebLink:

```python
class WebLinkConnection:
    """Class for handling WebLink connections and commands"""
    
    def __init__(self, host, port, use_tcp=True, timeout=2.0):
        """Initialize connection parameters"""
        self.host = host        # WebLink PC IP address
        self.port = port        # Port WebLink is listening on
        self.use_tcp = use_tcp  # TCP or UDP protocol
        self.timeout = timeout  # Connection timeout
        self.socket = None
    
    def connect(self):
        """Establish connection to WebLink"""
        # Create appropriate socket type
        socket_type = socket.SOCK_STREAM if self.use_tcp else socket.SOCK_DGRAM
        self.socket = socket.socket(socket.AF_INET, socket_type)
        self.socket.settimeout(self.timeout)
        
        # For TCP, establish connection
        if self.use_tcp:
            self.socket.connect((self.host, self.port))
    
    def send_message(self, message):
        """Send message to WebLink"""
        if not self.socket:
            self.connect()
        
        # Convert to bytes and send
        bytes_to_send = message.encode('utf-8')
        if self.use_tcp:
            self.socket.sendall(bytes_to_send)
        else:
            self.socket.sendto(bytes_to_send, (self.host, self.port))
    
    def send_command(self, command):
        """Send command to WebLink"""
        # Format according to WebLink standards
        formatted_command = f"eyecmd {command} endcmd"
        self.send_message(formatted_command)
    
    def disconnect(self):
        """Close connection to WebLink"""
        if self.socket:
            self.socket.close()
            self.socket = None
```

## 4. Integration with oTree

### 4.1. oTree Live Method Pattern

oTree uses LiveMethod to handle real-time communication with the browser:

```python
# In the Page class
@staticmethod
def live_method(player, data):
    # Route based on action type
    if data.get('action') == 'send_to_weblink':
        return player.send_to_weblink(data)
    # Other actions...

# In the Player class
def send_to_weblink(self, data):
    """Send message to WebLink from player action"""
    try:
        # Get configuration
        host = self.session.config.get('weblink_host', '127.0.0.1')
        port = self.session.config.get('weblink_port', 50700)
        use_tcp = self.session.config.get('weblink_use_tcp', True)
        
        # Create connection
        weblink = WebLinkConnection(host=host, port=port, use_tcp=use_tcp)
        
        # Send message
        message = data.get('message', 'DEFAULT_MESSAGE')
        weblink.send_message(message)
        weblink.disconnect()
        
        return {self.id_in_group: {'status': 'success'}}
    except Exception as e:
        return {self.id_in_group: {'status': 'error', 'message': str(e)}}
```

### 4.2. Experiment Settings Configuration

In your `settings.py` file, add WebLink configuration:

```python
SESSION_CONFIGS = [
    dict(
        name='your_experiment',
        app_sequence=['your_app'],
        # WebLink settings
        weblink_host='192.168.1.100',  # IP address of WebLink PC
        weblink_port=50700,            # Port WebLink is listening on
        weblink_use_tcp=True           # Use TCP instead of UDP
    ),
]
```

### 4.3. JavaScript Integration

In your HTML template:

```javascript
// Send event to WebLink via oTree
function sendToWebLink(message) {
    liveSend({
        'action': 'send_to_weblink',
        'message': message,
        'timestamp': Date.now()
    });
}

// Listen for response from oTree
liveRecv(function(data) {
    console.log("Response from server:", data);
    // Handle success/error feedback
});

// Example: Button click handler
document.getElementById('event-button').addEventListener('click', function() {
    sendToWebLink("EVENT_BUTTON_CLICKED");
});
```

## 5. Common Message Types

### 5.1. Trial Events

```python
# Mark start of trial
weblink.send_message(f"TRIALID {trial_number}")

# Mark stimulus presentation
weblink.send_message(f"SYNCTIME {timestamp}")

# Record user response
weblink.send_message(f"RESPONSE {response_value}")
```

### 5.2. Eye Tracker Commands

```python
# Start recording
weblink.send_command("start_recording")

# Stop recording
weblink.send_command("stop_recording")

# Initiate calibration
weblink.send_command("do_tracker_setup")

# Perform drift correction
weblink.send_command("do_drift_correct")
```

## 6. Important Considerations

### 6.1. Connection Requirements

1. **WebLink must be running first** before sending messages
2. "Listen for External TCP/UDP Messages" must be enabled in WebLink
3. Firewall must allow connections on the specified port
4. Network connectivity must exist between oTree server and WebLink PC

### 6.2. TCP vs. UDP Considerations

- **TCP**:
  - Guaranteed message delivery
  - Connection-oriented (requires established connection)
  - Better for important messages that must be received
  
- **UDP**:
  - Faster with less overhead
  - No connection establishment required
  - Better for high-frequency, less critical messages

### 6.3. Message Format

WebLink accepts two types of messages:
1. **Plain messages**: Recorded directly to EDF file
2. **Commands**: Start with "eyecmd" and end with "endcmd"

## 7. Debugging Tips

1. Ensure WebLink is properly configured to listen for external messages
2. Check network connectivity between servers
3. Verify firewall settings
4. Test with simple messages before implementing complex functionality
5. Use proper error handling in your code
6. Check EDF file after experiment to ensure messages were recorded

## 8. Sequence for Setup

1. Start WebLink experiment on Display PC
2. Enable "Listen for External TCP/UDP Messages" in WebLink settings
3. Start oTree server and experiment
4. Test connection before collecting data
5. Verify messages in EDF file after session 
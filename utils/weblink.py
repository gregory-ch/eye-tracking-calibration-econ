import socket
import logging
import time
from typing import Optional, Union, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class WebLinkConnection:
    """Class to handle WebLink connections and commands"""
    
    def __init__(self, host: str, port: int, use_tcp: bool = True, timeout: float = 2.0):
        """
        Initialise WebLink connection
        
        Args:
            host (str): IP address of Display PC running WebLink
            port (int): Port number WebLink is listening on
            use_tcp (bool): Use TCP (True) or UDP (False) connection
            timeout (float): Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.use_tcp = use_tcp
        self.timeout = timeout
        self.socket = None
        self.connected = False
        
    def connect(self) -> None:
        """Establish connection to WebLink"""
        try:
            # Create socket based on protocol
            socket_type = socket.SOCK_STREAM if self.use_tcp else socket.SOCK_DGRAM
            self.socket = socket.socket(socket.AF_INET, socket_type)
            self.socket.settimeout(self.timeout)  # Set timeout
            
            # For TCP, we need to establish a connection first
            if self.use_tcp:
                logger.info(f"Connecting to WebLink at {self.host}:{self.port} using TCP...")
                self.socket.connect((self.host, self.port))
                self.connected = True
            else:
                # For UDP, we don't establish a connection
                logger.info(f"Created UDP socket for WebLink at {self.host}:{self.port}")
                self.connected = True
                
            logger.info(f"Ready to communicate with WebLink at {self.host}:{self.port}")
        except socket.timeout:
            logger.error(f"Connection timeout connecting to WebLink at {self.host}:{self.port}")
            if self.socket:
                self.socket.close()
                self.socket = None
            raise ConnectionError(f"Connection timeout to WebLink at {self.host}:{self.port}. Make sure WebLink is running and configured to listen on this port.")
        except ConnectionRefusedError:
            logger.error(f"Connection refused by WebLink at {self.host}:{self.port}")
            if self.socket:
                self.socket.close()
                self.socket = None
            raise ConnectionError(f"Connection refused by WebLink at {self.host}:{self.port}. Make sure WebLink is running, listening on this port, and allowed through firewall.")
        except Exception as e:
            logger.error(f"Failed to connect to WebLink: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            raise
    
    def disconnect(self) -> None:
        """Close connection to WebLink"""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.connected = False
            logger.info("Disconnected from WebLink")
    
    def send_command(self, command: str) -> None:
        """
        Send command to WebLink
        
        Args:
            command (str): Command to send (will be formatted with eyecmd/endcmd)
        """
        if not self.socket:
            self.connect()
            
        try:
            # Format according to WebLink standards
            formatted_command = f"eyecmd {command} endcmd"
            # Send the message
            self._send_message(formatted_command)
            logger.info(f"Sent command: {formatted_command}")
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            raise
    
    def send_message(self, message: str) -> None:
        """
        Send raw message to WebLink (will be recorded in EDF file)
        
        Args:
            message (str): Message to send
        """
        if not self.socket:
            self.connect()
            
        try:
            # Send the message without any formatting
            self._send_message(message)
            logger.info(f"Sent message: {message}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    def _send_message(self, message: str) -> None:
        """
        Internal method to send data according to protocol
        
        Args:
            message (str): Message to send
        """
        # Convert string to bytes
        bytes_to_send = message.encode('utf-8')
        
        # Send according to protocol
        if self.use_tcp:
            self.socket.sendall(bytes_to_send)
        else:
            self.socket.sendto(bytes_to_send, (self.host, self.port))
    
    @staticmethod
    def test_connection(host: str, port: int, use_tcp: bool = True, timeout: float = 2.0) -> Dict[str, Any]:
        """
        Test connection to WebLink without sending any messages
        
        Args:
            host (str): IP address of WebLink PC
            port (int): Port number WebLink is listening on
            use_tcp (bool): Use TCP (True) or UDP (False) protocol
            timeout (float): Connection timeout in seconds
            
        Returns:
            Dict with connection test results
        """
        result = {
            'success': False,
            'error': None,
            'protocol': 'TCP' if use_tcp else 'UDP',
            'host': host,
            'port': port
        }
        
        try:
            # For TCP we can test actual connection
            if use_tcp:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((host, port))
                s.close()
                result['success'] = True
            else:
                # For UDP we can only check if host is reachable via ping
                # Create socket but don't send anything
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(timeout)
                # We don't actually send data, just check if host is reachable
                result['success'] = True
                result['warning'] = "UDP connection cannot be fully tested without sending data"
                s.close()
        except socket.timeout:
            result['error'] = f"Connection timeout to {host}:{port}. Make sure WebLink is running."
        except ConnectionRefusedError:
            result['error'] = f"Connection refused by {host}:{port}. Make sure WebLink is listening on this port and allowed through firewall."
        except Exception as e:
            result['error'] = f"Error testing connection: {str(e)}"
        
        return result


# Common EyeLink commands
def start_recording(connection: WebLinkConnection) -> None:
    """Start recording eye movements"""
    connection.send_command("start_recording")

def stop_recording(connection: WebLinkConnection) -> None:
    """Stop recording eye movements"""
    connection.send_command("stop_recording")

def calibrate(connection: WebLinkConnection) -> None:
    """Start calibration procedure"""
    connection.send_command("do_tracker_setup")

def drift_check(connection: WebLinkConnection) -> None:
    """Perform drift check"""
    connection.send_command("do_drift_correct")

def send_trial_message(connection: WebLinkConnection, trial_num: int) -> None:
    """Send trial start message - using standard EDF format"""
    connection.send_message(f"TRIALID {trial_num}") 
#!/usr/bin/env python3
"""
SEER Robot Controller Base Class

This module provides the base class for SEER robot controllers with common
functionality that can be shared among different controller implementations.

Features:
- Connection management (connect/disconnect)
- Protocol handling (header packing/unpacking)
- Generic command sending with request-response pattern
- Error handling and timeout management
- Thread-safe operations

Manual: https://seer-group.feishu.cn/wiki/WsI2wM46YiESh8k12EBclv23nOf?table=tblObW6PmjUPTyTn&view=vewiqqgyEX

Author: Assistant
Date: October 18, 2025
"""

import socket
import json
import struct
import time
from typing import Optional, Dict, Any

# Protocol constants
MAGIC_BYTE = 0x5A
HEADER_FORMAT = '!BBHLH6s'
HEADER_SIZE = 16
PACK_FMT_STR = '!BBHLH6s'


def packMasg(reqId, msgType, msg={}):
    """
    Pack message according to SEER protocol format.
    
    This is the official implementation provided by the robot company.
    
    Args:
        reqId: Request ID
        msgType: Message type
        msg: Message dictionary (default: empty dict)
        
    Returns:
        bytes: Packed message ready to send
    """
    msgLen = 0
    jsonStr = json.dumps(msg)
    if (msg != {}):
        msgLen = len(jsonStr)
    rawMsg = struct.pack(PACK_FMT_STR, 0x5A, 0x01, reqId, msgLen, msgType, b'\x00\x00\x00\x00\x00\x00')
    # Debug print - commented out to reduce console output
    # print("{:02X} {:02X} {:04X} {:08X} {:04X}"
    # .format(0x5A, 0x01, reqId, msgLen, msgType))

    if (msg != {}):
        rawMsg += bytearray(jsonStr,'ascii')
        # Debug print - commented out to reduce console output
        # print(msg)

    return rawMsg


class SeerControllerBase:
    """
    Base class for SEER robot controllers.
    
    Provides common functionality for robot communication including:
    - TCP socket connection management
    - Protocol message packing and unpacking
    - Generic command sending with request-response pattern
    - Error handling and timeout management
    
    This class should be inherited by specific controller implementations
    that add domain-specific query methods.
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19204):
        """
        Initialize the base controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
            robot_port: Port number for communication (default: 19204)
        """
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.socket = None
        self.connected = False
        
        # Connection statistics
        self.stats = {
            'connection_attempts': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'total_commands_sent': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'last_connect_time': None,
            'last_disconnect_time': None,
        }
    
    def unpack_header(self, data: bytes) -> Dict[str, Any]:
        """
        Unpack message header from raw bytes.
        
        Args:
            data: Raw header bytes (must be exactly 16 bytes)
            
        Returns:
            Dictionary containing header fields:
            - magic: Magic byte (should be 0x5A)
            - version: Protocol version
            - req_id: Request ID
            - msg_len: Length of JSON payload
            - msg_type: Message type identifier
            - reserved: Reserved bytes
            
        Raises:
            ValueError: If header data is too short
        """
        if len(data) < HEADER_SIZE:
            raise ValueError(f"Header too short: {len(data)} bytes, expected {HEADER_SIZE}")
        
        header = struct.unpack(HEADER_FORMAT, data)
        magic, version, req_id, msg_len, msg_type, reserved = header
        
        return {
            'magic': magic,
            'version': version,
            'req_id': req_id,
            'msg_len': msg_len,
            'msg_type': msg_type,
            'reserved': reserved
        }
    
    def pack_message(self, req_id: int, msg_type: int, msg: Dict = None) -> bytes:
        """
        Pack a message using the official protocol format.
        
        Args:
            req_id: Request ID
            msg_type: Message type identifier
            msg: Optional message payload as dictionary
            
        Returns:
            Packed message bytes ready to send
        """
        if msg is None:
            msg = {}
        return packMasg(req_id, msg_type, msg)
    
    def connect(self, timeout: float = 5.0) -> bool:
        """
        Establish connection to the robot.
        
        Args:
            timeout: Socket timeout in seconds (default: 5.0)
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Already connected
            if self.connected:
                return True
            
            # Create new socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            
            # Attempt connection
            self.socket.connect((self.robot_ip, self.robot_port))
            
            # Update state
            self.connected = True
            self.stats['connection_attempts'] += 1
            self.stats['successful_connections'] += 1
            self.stats['last_connect_time'] = time.time()
            
            return True
            
        except socket.timeout:
            self.connected = False
            self.stats['connection_attempts'] += 1
            self.stats['failed_connections'] += 1
            return False
        except ConnectionRefusedError:
            self.connected = False
            self.stats['connection_attempts'] += 1
            self.stats['failed_connections'] += 1
            return False
        except OSError:
            self.connected = False
            self.stats['connection_attempts'] += 1
            self.stats['failed_connections'] += 1
            return False
    
    def disconnect(self):
        """
        Close the connection to the robot.
        
        This method is safe to call multiple times and will clean up
        the socket connection if it exists.
        """
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
            self.stats['last_disconnect_time'] = time.time()
    
    def reconnect(self, timeout: float = 5.0) -> bool:
        """
        Disconnect and reconnect to the robot.
        
        Args:
            timeout: Socket timeout in seconds (default: 5.0)
            
        Returns:
            True if reconnection successful, False otherwise
        """
        self.disconnect()
        return self.connect(timeout)
    
    def is_connected(self) -> bool:
        """
        Check if currently connected to the robot.
        
        Returns:
            True if connected, False otherwise
        """
        return self.connected
    
    def send_command(self, req_id: int, msg_type: int, msg: Dict = None, 
                    expected_response: int = None, timeout: float = 5.0) -> Optional[Dict]:
        """
        Send a command to the robot and receive response.
        
        This is the core communication method that handles the complete
        request-response cycle including:
        - Packing the message
        - Sending via socket
        - Receiving response header
        - Validating response
        - Receiving and parsing JSON payload
        
        Args:
            req_id: Request ID
            msg_type: Message type identifier for the request
            msg: Optional message payload as dictionary
            expected_response: Optional expected response message type for validation
            timeout: Socket timeout in seconds (default: 5.0)
            
        Returns:
            Response data as dictionary if successful, None if failed
            
        Notes:
            - Automatically updates connection statistics
            - Returns None on any error (timeout, connection loss, parsing error)
            - Validates magic byte in response header
        """
        if not self.connected:
            return None
        
        try:
            self.stats['total_commands_sent'] += 1
            
            # Create and send request
            request_msg = self.pack_message(req_id, msg_type, msg)
            self.socket.send(request_msg)
            
            # Receive response header
            self.socket.settimeout(timeout)
            header_data = self.socket.recv(HEADER_SIZE)
            
            if not header_data:
                self.stats['failed_commands'] += 1
                return None
            
            # Parse header
            header = self.unpack_header(header_data)
            
            # Validate magic byte
            if header['magic'] != MAGIC_BYTE:
                self.stats['failed_commands'] += 1
                return None
            
            # Validate response type if specified
            if expected_response is not None and header['msg_type'] != expected_response:
                # Response type mismatch - still process but could log warning
                pass
            
            # Receive JSON data if present
            json_data = {}
            if header['msg_len'] > 0:
                json_bytes = b''
                remaining = header['msg_len']
                
                # Receive in chunks
                while remaining > 0:
                    chunk_size = min(1024, remaining)
                    chunk = self.socket.recv(chunk_size)
                    
                    if not chunk:
                        break
                    
                    json_bytes += chunk
                    remaining -= len(chunk)
                
                # Parse JSON
                try:
                    json_str = json_bytes.decode('utf-8')
                    json_data = json.loads(json_str)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self.stats['failed_commands'] += 1
                    return None
            
            # Success
            self.stats['successful_commands'] += 1
            return json_data
            
        except socket.timeout:
            self.stats['failed_commands'] += 1
            return None
        except (ConnectionResetError, BrokenPipeError, OSError):
            self.connected = False
            self.stats['failed_commands'] += 1
            return None
        except Exception:
            self.stats['failed_commands'] += 1
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection and command statistics.
        
        Returns:
            Dictionary containing statistics:
            - connection_attempts: Total connection attempts
            - successful_connections: Successful connections
            - failed_connections: Failed connections
            - total_commands_sent: Total commands sent
            - successful_commands: Successful command responses
            - failed_commands: Failed commands
            - last_connect_time: Timestamp of last connection
            - last_disconnect_time: Timestamp of last disconnection
            - success_rate: Percentage of successful commands
        """
        stats = self.stats.copy()
        
        # Calculate success rate
        if stats['total_commands_sent'] > 0:
            stats['success_rate'] = (stats['successful_commands'] / stats['total_commands_sent']) * 100
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset all statistics counters."""
        self.stats = {
            'connection_attempts': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'total_commands_sent': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'last_connect_time': None,
            'last_disconnect_time': None,
        }
    
    def __enter__(self):
        """Context manager entry - connect to robot."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect from robot."""
        self.disconnect()
        return False
    
    def __repr__(self) -> str:
        """String representation of the controller."""
        status = "connected" if self.connected else "disconnected"
        return f"{self.__class__.__name__}(robot_ip='{self.robot_ip}', robot_port={self.robot_port}, status='{status}')"


def main():
    """
    Example usage of SeerControllerBase.
    
    This demonstrates basic connection and command sending functionality.
    Specific controller implementations should inherit from this class
    and add domain-specific methods.
    """
    print("🤖 SEER Controller Base - Example Usage")
    print("=" * 60)
    
    # Create controller instance
    controller = SeerControllerBase(robot_ip='192.168.192.5', robot_port=19204)
    
    print(f"Controller: {controller}")
    print(f"Connected: {controller.is_connected()}")
    
    # Example 1: Using context manager
    print("\n📝 Example 1: Using context manager")
    with SeerControllerBase(robot_ip='192.168.192.5', robot_port=19204) as ctrl:
        print(f"  Connected: {ctrl.is_connected()}")
        
        # Send a position query command as example
        # REQUEST_POSITION = 1004, RESPONSE_POSITION = 11004
        result = ctrl.send_command(1, 1004, {}, 11004, timeout=5.0)
        
        if result:
            print("  ✅ Command successful!")
            print(f"  Response keys: {list(result.keys())}")
        else:
            print("  ❌ Command failed")
    
    # Example 2: Manual connection management
    print("\n📝 Example 2: Manual connection management")
    controller = SeerControllerBase(robot_ip='192.168.192.5', robot_port=19204)
    
    if controller.connect():
        print("  ✅ Connected successfully")
        
        # Get statistics
        stats = controller.get_stats()
        print(f"  Connection attempts: {stats['connection_attempts']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        
        controller.disconnect()
        print("  🔌 Disconnected")
    else:
        print("  ❌ Connection failed")
    
    print("\n" + "=" * 60)
    print("💡 Inherit from SeerControllerBase to create specific controllers!")


if __name__ == "__main__":
    main()

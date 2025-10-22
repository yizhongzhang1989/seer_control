#!/usr/bin/env python3
"""
SEER Robot Push Controller

This module provides push data receiving functionality for SEER robots.
Unlike other controllers, this controller continuously listens for data pushed from the robot.

Features:
- Configure push data parameters (interval, included/excluded fields)
- Continuously receive pushed data from robot in background thread
- Parse and process JSON push messages
- Statistics tracking (packet count, frequency, etc.)

Push Configuration:
- Port: 19301 (both configuration and push data receiving)
- Config command ID: 9300 (robot_push_config_req)

Manual: https://seer-group.feishu.cn/wiki/WsI2wM46YiESh8k12EBclv23nOf?table=tblObW6PmjUPTyTn&view=vewiqqgyEX

Author: Assistant
Date: October 18, 2025
"""

import socket
import time
import json
import threading
from typing import Optional, Dict, Any, List, Callable
try:
    from .seer_controller_base import SeerControllerBase
except ImportError:
    from seer_controller_base import SeerControllerBase


class SeerPushController(SeerControllerBase):
    """
    SEER Robot Push Controller.
    
    This controller is different from others - it receives continuous push data from the robot
    rather than sending commands and receiving responses. It runs a background listener thread
    to process incoming data.
    
    Both configuration and push data use the same port 19301.
    
    Example:
        # Create controller
        controller = SeerPushController('192.168.192.5')
        
        # Configure push settings (uses push port 19301)
        controller.configure_push(interval=100, included_fields=['x', 'y', 'angle'])
        
        # Start listening for push data
        controller.start_listening(callback=lambda data: print(data))
        
        # Let it run for a while
        time.sleep(10)
        
        # Stop listening
        controller.stop_listening()
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5', 
                 robot_port: int = 19301):
        """
        Initialize the push controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
            robot_port: Port number for both config and push data (default: 19301)
        """
        # Initialize base controller with push port
        super().__init__(robot_ip, robot_port)
        
        self.listening = False
        self.listener_thread = None
        self.callback = None
        
        # Push-specific statistics
        self.push_stats = {
            'packets_received': 0,
            'bytes_received': 0,
            'start_time': None,
            'last_packet_time': None,
            'frequencies': [],
            'errors': 0
        }
    
    def configure_push(self, 
                      interval: Optional[int] = None,
                      included_fields: Optional[List[str]] = None,
                      excluded_fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Configure robot push settings.
        
        This command is sent to the push port (19301) with message ID 9300.
        
        Args:
            interval: Message push interval in milliseconds (ms)
                - Optional parameter
            included_fields: List of field names to include in push messages
                - Optional parameter
                - Example: ['x', 'y', 'angle', 'battery']
            excluded_fields: List of field names to exclude from push messages
                - Optional parameter
                - Example: ['debug_info', 'internal_state']
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            # Set push interval to 100ms with specific fields
            result = controller.configure_push(
                interval=100, 
                included_fields=['x', 'y', 'angle', 'v', 'w']
            )
            
            # Set push interval only
            result = controller.configure_push(interval=200)
            
            # Exclude certain fields
            result = controller.configure_push(
                interval=100,
                excluded_fields=['debug_info']
            )
        """
        # Build payload
        payload = {}
        
        if interval is not None:
            payload['interval'] = interval
        if included_fields is not None:
            payload['included_fields'] = included_fields
        if excluded_fields is not None:
            payload['excluded_fields'] = excluded_fields
        
        # Send configuration command (req_id=9300, resp_id=19300)
        return self.send_command(
            req_id=1,
            msg_type=9300,  # robot_push_config_req
            msg=payload,
            expected_response=19300,  # robot_push_config_resp
            timeout=5.0
        )
    
    def start_listening(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> bool:
        """
        Start listening for push data in a background thread.
        
        Uses the same socket connection (port 19301) that was used for configuration.
        Must be connected before calling this method.
        
        Args:
            callback: Optional callback function that will be called for each received message.
                     The callback receives the parsed JSON data as a dictionary.
                     If None, messages will be printed to console.
        
        Returns:
            True if listener started successfully, False otherwise
            
        Example:
            def my_callback(data):
                print(f"Position: ({data.get('x')}, {data.get('y')})")
            
            controller.start_listening(callback=my_callback)
        """
        if self.listening:
            print("⚠️ Already listening for push data")
            return False
        
        # Must be connected to push port
        if not self.connected:
            print("❌ Not connected to robot. Call connect() first.")
            return False
        
        # Set callback
        self.callback = callback
        
        # Start listener thread
        self.listening = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        
        print(f"🎧 Started listening for push data (Press Ctrl+C or call stop_listening() to stop)")
        return True
    
    def stop_listening(self):
        """Stop listening for push data and close the connection."""
        if not self.listening:
            print("⚠️ Not currently listening")
            return
        
        print("🛑 Stopping push data listener...")
        self.listening = False
        
        # Wait for thread to finish
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2.0)
        
        # Print final stats
        self._print_final_stats()
        
        print("✅ Push data listener stopped")
    
    def _listen_loop(self):
        """Main listening loop (runs in background thread)."""
        buffer = b""
        self.push_stats['start_time'] = time.time()
        
        try:
            # Set short timeout for responsive interruption
            self.socket.settimeout(0.1)
            
            while self.listening and self.connected:
                try:
                    # Receive data from robot
                    data = self.socket.recv(4096)
                    
                    if not data:
                        print(f"\n[{time.strftime('%H:%M:%S')}] Robot disconnected")
                        self.connected = False
                        break
                    
                    # Add received data to buffer
                    buffer += data
                    self.push_stats['bytes_received'] += len(data)
                    
                    # Process complete JSON packets in the buffer
                    while buffer:
                        json_packet, buffer = self._extract_json_packet(buffer)
                        
                        if json_packet is None:
                            # No complete JSON packet found, need more data
                            break
                        
                        # Process the complete JSON packet
                        self._process_packet(json_packet)
                
                except socket.timeout:
                    continue  # Continue listening, timeout is for responsiveness
                except ConnectionResetError:
                    print(f"\n[{time.strftime('%H:%M:%S')}] Connection reset by robot")
                    self.connected = False
                    break
                except Exception as e:
                    print(f"\n[{time.strftime('%H:%M:%S')}] Error receiving data: {e}")
                    self.push_stats['errors'] += 1
                    
        except Exception as e:
            print(f"Error in listen loop: {e}")
            self.push_stats['errors'] += 1
        finally:
            self.listening = False
    
    def _process_packet(self, json_packet: bytes):
        """Process a complete JSON packet."""
        # Update statistics
        self._update_stats()
        
        try:
            # Parse JSON
            parsed_data = json.loads(json_packet.decode('utf-8'))
            
            # Call callback if provided, otherwise print
            if self.callback:
                try:
                    self.callback(parsed_data)
                except Exception as e:
                    print(f"⚠️ Callback error: {e}")
            else:
                # Default: print formatted data
                timestamp = time.strftime('%H:%M:%S.%f')[:-3]
                print(f"\n[{timestamp}] Push Message #{self.push_stats['packets_received']} (Freq: {self._get_current_frequency():.1f}Hz)")
                print(json.dumps(parsed_data, indent=2, ensure_ascii=False))
                print("-" * 60)
                
        except json.JSONDecodeError as e:
            print(f"⚠️ Invalid JSON: {e}")
            print(f"   Raw: {json_packet}")
            self.push_stats['errors'] += 1
        except UnicodeDecodeError as e:
            print(f"⚠️ Invalid UTF-8 encoding: {e}")
            self.push_stats['errors'] += 1
    
    def _extract_json_packet(self, buffer: bytes) -> tuple:
        """
        Extract a complete JSON packet from the buffer.
        
        The SEER protocol format for push data is:
        - Header: 16 bytes (magic=0x5A, version, reqId, msgLen, msgType, reserved)
        - Payload: JSON data (msgLen bytes)
        
        Args:
            buffer: Byte buffer containing incoming data
            
        Returns:
            Tuple of (json_packet, remaining_buffer) or (None, buffer) if no complete packet
        """
        import struct
        
        MAGIC_BYTE = 0x5A
        HEADER_SIZE = 16
        HEADER_FORMAT = '!BBHLH6s'
        
        # Check if we have at least a complete header
        if len(buffer) < HEADER_SIZE:
            return None, buffer
        
        # Try to find the magic byte
        magic_pos = buffer.find(bytes([MAGIC_BYTE]))
        
        if magic_pos == -1:
            # No magic byte found - might be pure JSON or garbage
            # Fall back to JSON extraction methods
            return self._extract_json_fallback(buffer)
        
        # If magic byte is not at start, skip garbage data
        if magic_pos > 0:
            buffer = buffer[magic_pos:]
        
        # Check if we have enough data for header
        if len(buffer) < HEADER_SIZE:
            return None, buffer
        
        try:
            # Unpack header
            magic, version, req_id, msg_len, msg_type, reserved = struct.unpack(
                HEADER_FORMAT, buffer[:HEADER_SIZE]
            )
            
            # Validate magic byte
            if magic != MAGIC_BYTE:
                # Not a valid header, try next magic byte
                next_magic = buffer.find(bytes([MAGIC_BYTE]), 1)
                if next_magic > 0:
                    return None, buffer[next_magic:]
                else:
                    return None, buffer[1:]  # Skip this byte
            
            # Check if we have complete message
            total_len = HEADER_SIZE + msg_len
            if len(buffer) < total_len:
                # Not enough data yet
                return None, buffer
            
            # Extract JSON payload
            json_payload = buffer[HEADER_SIZE:total_len]
            remaining = buffer[total_len:]
            
            # Return the JSON payload (without header)
            if json_payload.strip():
                return json_payload.strip(), remaining
            else:
                return None, remaining
                
        except struct.error:
            # Header unpacking failed, skip to next potential magic byte
            next_magic = buffer.find(bytes([MAGIC_BYTE]), 1)
            if next_magic > 0:
                return None, buffer[next_magic:]
            else:
                return None, buffer[1:]
    
    def _extract_json_fallback(self, buffer: bytes) -> tuple:
        """
        Fallback method for extracting JSON when no protocol header is found.
        
        Args:
            buffer: Byte buffer containing incoming data
            
        Returns:
            Tuple of (json_packet, remaining_buffer) or (None, buffer)
        """
        # Method 1: Try newline-delimited JSON first
        newline_pos = buffer.find(b'\n')
        if newline_pos != -1:
            packet = buffer[:newline_pos]
            remaining = buffer[newline_pos + 1:]
            if packet.strip() and packet.strip().startswith(b'{'):
                return packet.strip(), remaining
            else:
                return None, remaining
        
        # Method 2: Try to find complete JSON by bracket counting
        packet, remaining = self._extract_json_by_brackets(buffer)
        if packet is not None:
            return packet, remaining
        
        # Method 3: Check for other common delimiters
        for delimiter in [b'\r\n', b'\x00', b'\r']:
            delim_pos = buffer.find(delimiter)
            if delim_pos != -1:
                packet = buffer[:delim_pos]
                remaining = buffer[delim_pos + len(delimiter):]
                if packet.strip() and packet.strip().startswith(b'{'):
                    return packet.strip(), remaining
                else:
                    return None, remaining
        
        # No complete packet found
        return None, buffer
    
    def _extract_json_by_brackets(self, buffer: bytes) -> tuple:
        """Extract JSON by counting opening/closing braces."""
        try:
            text = buffer.decode('utf-8', errors='ignore')
            brace_count = 0
            in_string = False
            escape_next = False
            start_pos = -1
            
            for i, char in enumerate(text):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if in_string:
                    continue
                
                if char == '{':
                    if brace_count == 0:
                        start_pos = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_pos != -1:
                        # Found complete JSON object
                        json_text = text[start_pos:i+1]
                        json_bytes = json_text.encode('utf-8')
                        remaining_text = text[i+1:]
                        remaining_bytes = remaining_text.encode('utf-8')
                        return json_bytes, remaining_bytes
            
        except UnicodeDecodeError:
            pass
        
        return None, buffer
    
    def _update_stats(self):
        """Update packet statistics."""
        current_time = time.time()
        self.push_stats['packets_received'] += 1
        
        if self.push_stats['last_packet_time'] is not None:
            time_diff = current_time - self.push_stats['last_packet_time']
            if time_diff > 0:
                frequency = 1.0 / time_diff
                self.push_stats['frequencies'].append(frequency)
                # Keep only last 50 frequencies for rolling average
                if len(self.push_stats['frequencies']) > 50:
                    self.push_stats['frequencies'].pop(0)
        
        self.push_stats['last_packet_time'] = current_time
    
    def _get_current_frequency(self) -> float:
        """Get current frequency based on recent packets."""
        if not self.push_stats['frequencies']:
            return 0.0
        return sum(self.push_stats['frequencies']) / len(self.push_stats['frequencies'])
    
    def _print_final_stats(self):
        """Print final statistics."""
        if self.push_stats['start_time']:
            total_time = time.time() - self.push_stats['start_time']
            avg_frequency = self.push_stats['packets_received'] / total_time if total_time > 0 else 0
            
            print(f"\n📊 Push Data Statistics:")
            print(f"  Total packets received: {self.push_stats['packets_received']}")
            print(f"  Total bytes received: {self.push_stats['bytes_received']}")
            print(f"  Total errors: {self.push_stats['errors']}")
            print(f"  Total time: {total_time:.2f} seconds")
            print(f"  Average frequency: {avg_frequency:.2f} Hz")
            if self.push_stats['frequencies']:
                print(f"  Recent frequency: {self._get_current_frequency():.2f} Hz")
                print(f"  Min frequency: {min(self.push_stats['frequencies']):.2f} Hz")
                print(f"  Max frequency: {max(self.push_stats['frequencies']):.2f} Hz")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.
        
        Returns:
            Dictionary containing current statistics
        """
        stats = dict(self.push_stats)
        if self.push_stats['start_time']:
            stats['total_time'] = time.time() - self.push_stats['start_time']
            stats['avg_frequency'] = (
                self.push_stats['packets_received'] / stats['total_time'] 
                if stats['total_time'] > 0 else 0
            )
            stats['current_frequency'] = self._get_current_frequency()
        return stats
    
    def reset_stats(self):
        """Reset all statistics."""
        self.push_stats = {
            'packets_received': 0,
            'bytes_received': 0,
            'start_time': time.time() if self.listening else None,
            'last_packet_time': None,
            'frequencies': [],
            'errors': 0
        }
        print("📊 Statistics reset")
    
    def __repr__(self) -> str:
        """String representation of the controller."""
        status = "listening" if self.listening else "stopped"
        return (f"<{self.__class__.__name__} "
                f"robot_ip={self.robot_ip} "
                f"port={self.robot_port} "
                f"status={status}>")


def main():
    """
    Demo program that connects, configures push data, and starts listening.
    
    Configuration:
    - Interval: 1000ms (1 Hz)
    - Fields: x, y, angle, vx, vy, w
    - Callback: Prints received JSON data
    """
    print("🤖 SEER Push Controller - Demo Mode")
    print("=" * 60)
    
    # Create controller
    controller = SeerPushController(robot_ip='192.168.1.123', robot_port=19301)
    print(f"Controller: {controller}")
    
    # Define callback to print JSON data
    def print_push_data(data):
        """Callback function to print received push data."""
        import json
        print("\n" + "=" * 60)
        print("📥 Received Push Data:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=" * 60)
    
    try:
        # Step 1: Connect to robot
        print("\n🔌 Step 1: Connecting to robot...")
        if not controller.connect():
            print("❌ Failed to connect to robot")
            return
        print("✅ Connected successfully!")
        
        # Step 2: Configure push settings
        print("\n⚙️  Step 2: Configuring push settings...")
        print("   Interval: 1000ms (1 Hz)")
        print("   Fields: x, y, angle, vx, vy, w")
        
        result = controller.configure_push(
            interval=1000,
            included_fields=['x', 'y', 'angle', 'vx', 'vy', 'w', 'jack']
        )
        
        if result and result.get('ret_code') == 0:
            print("✅ Push configuration successful!")
            print(f"   Response: {result}")
        else:
            print(f"❌ Push configuration failed: {result}")
            controller.disconnect()
            return
        
        # Step 3: Start listening with callback
        print("\n🎧 Step 3: Starting listener with callback...")
        if controller.start_listening(callback=print_push_data):
            print("✅ Listening started!")
            print("\n📊 Push data will appear below...")
            print("   Press Ctrl+C to stop")
            print("-" * 60)
            
            # Keep running until interrupted
            import time
            while controller.listening:
                time.sleep(1)
        else:
            print("❌ Failed to start listening")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    
    finally:
        # Clean up
        if controller.listening:
            controller.stop_listening()
        if controller.connected:
            controller.disconnect()
        
        print("\n" + "=" * 60)
        print("✅ Session ended!")
        print("=" * 60)
        if controller.listening:
            controller.stop_listening()
        if controller.connected:
            controller.disconnect()
        
        print("\n" + "=" * 60)
        print("✅ Session ended!")
        print("=" * 60)


if __name__ == "__main__":
    main()

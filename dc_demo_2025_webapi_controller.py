#!/usr/bin/env python3
"""
DC Demo 2025 Web API Controller - Remote Control via Web Interface

This module provides a controller class that controls the robot through the
web API instead of direct TCP connection. It simulates clicking buttons on
the web interface by making HTTP requests to the Flask web server.

This is useful for:
- Remote control from different machines
- Testing the web API programmatically
- Integrating robot control into other applications
- Avoiding direct robot connection conflicts

Author: Assistant
Date: October 23, 2025
"""

import requests
from typing import Dict, Any, List, Optional


class DCDemo2025WebAPIController:
    """
    DC Demo 2025 Web API Controller - Control robot through web interface.
    
    This class provides the same interface as DCDemo2025Controller but operates
    through HTTP requests to the web API instead of direct TCP connection.
    
    Features:
    - Same navigate() and goto_navigate_start() interface as DCDemo2025Controller
    - Retrieves trajectory list from web interface
    - All operations through HTTP REST API
    - No direct robot connection needed
    
    Examples:
        # Initialize with web URL
        controller = DCDemo2025WebAPIController("http://localhost:5000")
        
        # Check if robot is connected (on server side)
        if controller.is_connected():
            # Navigate using trajectory name
            result = controller.navigate("looptest")
            
            # Go to start position
            result = controller.goto_navigate_start("arm_dock2rack")
            
            # Get trajectory list
            trajectories = controller.get_trajectories()
            print(f"Available: {trajectories}")
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Initialize the Web API Controller.
        
        Args:
            base_url: Base URL of the web interface (e.g., "http://localhost:5000")
                     Should include protocol (http/https) and port if not default
        """
        self.base_url = base_url.rstrip('/')
        self._trajectories = None
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                      timeout: float = 10.0) -> Dict[str, Any]:
        """
        Make an HTTP request to the web API.
        
        Args:
            method: HTTP method ('GET' or 'POST')
            endpoint: API endpoint (e.g., '/api/status')
            data: Optional data for POST requests
            timeout: Request timeout in seconds (default: 10.0)
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            requests.exceptions.RequestException: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # Connection Status
    # ========================================================================
    
    def is_connected(self) -> bool:
        """
        Check if robot is connected (on server side).
        
        Returns:
            True if server is connected to robot, False otherwise
            
        Examples:
            if controller.is_connected():
                print("Robot is connected")
        """
        result = self._make_request('GET', '/api/status')
        return result.get('connected', False)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get connection status and robot IP.
        
        Returns:
            Dictionary with 'connected' and 'robot_ip' keys
            
        Examples:
            status = controller.get_status()
            print(f"Connected: {status['connected']}")
            print(f"Robot IP: {status['robot_ip']}")
        """
        return self._make_request('GET', '/api/status')
    
    # ========================================================================
    # Trajectory Management
    # ========================================================================
    
    def get_trajectories(self, force_refresh: bool = False) -> List[str]:
        """
        Get list of available trajectories from web interface.
        
        The trajectory list is cached after first retrieval. Use force_refresh=True
        to reload from server.
        
        Args:
            force_refresh: If True, reload trajectory list from server
            
        Returns:
            List of trajectory names
            
        Examples:
            trajectories = controller.get_trajectories()
            print(f"Available: {trajectories}")
            
            # Force refresh from server
            trajectories = controller.get_trajectories(force_refresh=True)
        """
        if self._trajectories is None or force_refresh:
            result = self._make_request('GET', '/api/trajectories')
            if result.get('success', False):
                self._trajectories = result.get('trajectories', [])
            else:
                self._trajectories = []
        
        return self._trajectories
    
    # ========================================================================
    # Navigation Functions
    # ========================================================================
    
    def navigate(self, trajectory: str, wait: bool = True, timeout: float = 600.0) -> Dict[str, Any]:
        """
        Execute a navigation task using a predefined trajectory.
        
        This simulates clicking a trajectory button on the web interface.
        
        Args:
            trajectory: Name of the trajectory to execute. Get available trajectories
                       using get_trajectories() method.
            wait: If True, waits for navigation completion (blocking). 
                  If False, returns immediately after starting (non-blocking).
            timeout: Maximum time to wait for task completion in seconds 
                    (default: 600.0, only used if wait=True)
        
        Returns:
            Dictionary with:
            - success (bool): True if navigation started successfully
            - task_id (str): Task ID assigned by robot
            - blocking (bool): Whether method waited for completion
            - message (str): Status message
            
        Examples:
            # Blocking navigation (waits for completion)
            result = controller.navigate("looptest")
            if result['success']:
                print(f"Navigation completed: {result['task_id']}")
            
            # Non-blocking navigation (returns immediately)
            result = controller.navigate("arm_dock2rack", wait=False)
            if result['success']:
                print(f"Navigation started: {result['task_id']}")
            
            # Custom timeout
            result = controller.navigate("courier_dock2rack", timeout=300.0)
        """
        data = {
            'trajectory': trajectory,
            'wait': wait,
            'timeout': timeout
        }
        
        # Calculate HTTP timeout: navigation timeout + 30 seconds buffer for network overhead
        # If wait=False, use short timeout since server responds immediately
        http_timeout = 30.0 if not wait else (timeout + 30.0)
        
        result = self._make_request('POST', '/api/navigate', data, timeout=http_timeout)
        
        # Add blocking flag to match DCDemo2025Controller interface
        if 'blocking' not in result:
            result['blocking'] = wait
        
        return result
    
    def goto_navigate_start(self, trajectory: str, wait: bool = True, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Navigate to the starting position of a trajectory.
        
        This simulates clicking the "Go to Start" button for a trajectory on the web interface.
        
        Args:
            trajectory: Name of the trajectory. Get available trajectories
                       using get_trajectories() method.
            wait: If True, waits for navigation completion (blocking). 
                  If False, returns immediately after starting (non-blocking).
            timeout: Maximum time to wait for navigation completion in seconds 
                    (default: 60.0, only used if wait=True)
        
        Returns:
            Dictionary with:
            - success (bool): True if navigation to start position completed/started successfully
            - task_id (str): Task ID assigned by robot
            - blocking (bool): Whether method waited for completion
            - start_position (str): The identified start position
            - message (str): Status message
            
        Examples:
            # Navigate to starting position of looptest trajectory
            result = controller.goto_navigate_start("looptest")
            if result['success']:
                print(f"At start position: {result['start_position']}")
            
            # Then execute the trajectory
            result = controller.navigate("looptest")
            
            # Non-blocking
            result = controller.goto_navigate_start("arm_dock2rack", wait=False)
        """
        data = {
            'trajectory': trajectory,
            'wait': wait,
            'timeout': timeout
        }
        
        # Calculate HTTP timeout: navigation timeout + 30 seconds buffer
        http_timeout = 30.0 if not wait else (timeout + 30.0)
        
        result = self._make_request('POST', '/api/goto_navigate_start', data, timeout=http_timeout)
        
        # Add blocking flag to match DCDemo2025Controller interface
        if 'blocking' not in result:
            result['blocking'] = wait
        
        return result
    
    # ========================================================================
    # Basic Navigation Functions
    # ========================================================================
    
    def goto(self, target_id: str, wait: bool = True, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Navigate to a specific location ID.
        
        Args:
            target_id: Target location identifier (e.g., "LM2", "AP8", "CP0")
            wait: If True, waits for navigation completion (blocking)
            timeout: Maximum time to wait for completion in seconds
        
        Returns:
            Dictionary with success status and task information
            
        Examples:
            result = controller.goto("LM2")
            result = controller.goto("AP8", wait=False)
        """
        data = {
            'target_id': target_id,
            'wait': wait,
            'timeout': timeout
        }
        
        # Calculate HTTP timeout: navigation timeout + 30 seconds buffer
        http_timeout = 30.0 if not wait else (timeout + 30.0)
        
        return self._make_request('POST', '/api/goto', data, timeout=http_timeout)
    
    def goto_charge(self, via_point: str = "LM2", charge_point: str = "CP0", 
                    wait: bool = False, timeout: float = 300.0) -> Dict[str, Any]:
        """
        Navigate to charging station.
        
        Args:
            via_point: Intermediate waypoint to pass through (default: "LM2")
            charge_point: Charging station location ID (default: "CP0")
            wait: If True, waits for navigation completion
            timeout: Maximum time to wait for completion in seconds
        
        Returns:
            Dictionary with success status and task information
            
        Examples:
            result = controller.goto_charge()
            result = controller.goto_charge(via_point="LM5", charge_point="CP1")
        """
        data = {
            'via_point': via_point,
            'charge_point': charge_point,
            'wait': wait,
            'timeout': timeout
        }
        
        # Calculate HTTP timeout: navigation timeout + 30 seconds buffer
        http_timeout = 30.0 if not wait else (timeout + 30.0)
        
        return self._make_request('POST', '/api/goto_charge', data, timeout=http_timeout)
    
    # ========================================================================
    # Task Control Functions
    # ========================================================================
    
    def pause_task(self) -> Dict[str, Any]:
        """
        Pause the current task.
        
        Returns:
            Dictionary with success status and message
            
        Examples:
            result = controller.pause_task()
        """
        return self._make_request('POST', '/api/pause_task')
    
    def resume_task(self) -> Dict[str, Any]:
        """
        Resume the current task.
        
        Returns:
            Dictionary with success status and message
            
        Examples:
            result = controller.resume_task()
        """
        return self._make_request('POST', '/api/resume_task')
    
    def cancel_task(self) -> Dict[str, Any]:
        """
        Cancel the current task.
        
        Returns:
            Dictionary with success status and message
            
        Examples:
            result = controller.cancel_task()
        """
        return self._make_request('POST', '/api/cancel_task')
    
    # ========================================================================
    # Emergency Controls
    # ========================================================================
    
    def emergency_stop(self) -> Dict[str, Any]:
        """
        Trigger emergency stop.
        
        Returns:
            Dictionary with success status and message
            
        Examples:
            result = controller.emergency_stop()
        """
        return self._make_request('POST', '/api/emergency_stop')
    
    def emergency_recover(self) -> Dict[str, Any]:
        """
        Recover from emergency stop.
        
        Returns:
            Dictionary with success status and message
            
        Examples:
            result = controller.emergency_recover()
        """
        return self._make_request('POST', '/api/emergency_recover')
    
    # ========================================================================
    # Status Query Functions
    # ========================================================================
    
    def task_status(self) -> Optional[int]:
        """
        Get current task status.
        
        Returns:
            Task status code (0=NONE, 1=WAITING, 2=RUNNING, 3=SUSPENDED,
            4=COMPLETED, 5=FAILED, 6=CANCELED) or None if error
            
        Examples:
            status = controller.task_status()
            if status == 2:
                print("Task is running")
        """
        result = self._make_request('GET', '/api/task_status')
        if result.get('success', False):
            return result.get('task_status')
        return None
    
    def get_push_data(self) -> Dict[str, Any]:
        """
        Get latest push data from robot.
        
        Returns:
            Dictionary containing push data (position, battery, jack state, etc.)
            
        Examples:
            data = controller.get_push_data()
            print(f"Battery: {data['battery_level']}%")
            print(f"Position: {data['current_station']}")
        """
        result = self._make_request('GET', '/api/push_data')
        if result.get('success', False):
            return result.get('data', {})
        return {}


# ============================================================================
# Command Line Interface
# ============================================================================

def main():
    """
    Main interactive loop for DCDemo2025WebAPIController.
    
    Provides a command-line interface for controlling the SEER robot
    through the web API.
    """
    print("="*60)
    print("🌐 DC Demo 2025 Web API Controller - Remote Control")
    print("="*60)
    
    # Get web URL
    web_url = input("\n🌐 Enter web interface URL (default: http://localhost:5000): ").strip()
    if not web_url:
        web_url = "http://localhost:5000"
    
    # Initialize controller
    controller = DCDemo2025WebAPIController(web_url)
    
    # Check connection status
    print(f"\n🔌 Checking connection to {web_url}...")
    try:
        status = controller.get_status()
        if status.get('connected', False):
            print(f"✅ Robot is connected (IP: {status.get('robot_ip')})")
        else:
            print("⚠️  Robot is not connected on server side")
            print("   Please connect through web interface first")
    except Exception as e:
        print(f"❌ Failed to connect to web server: {e}")
        print("   Make sure the web server is running")
        return
    
    # Load trajectories
    print("\n📋 Loading available trajectories...")
    trajectories = controller.get_trajectories()
    if trajectories:
        print(f"✅ Found {len(trajectories)} trajectories:")
        for traj in trajectories:
            print(f"   - {traj}")
    else:
        print("⚠️  No trajectories available")
    
    print("\n📝 Available commands:")
    print("  - navigate trajectory=<name>  (execute full trajectory)")
    print("  - goto_navigate_start trajectory=<name>  (go to trajectory start)")
    print("  - goto target_id=<id>  (navigate to specific location)")
    print("  - goto_charge  (navigate to charging station)")
    print("  - pause_task, resume_task, cancel_task  (task controls)")
    print("  - emergency_stop, emergency_recover  (emergency controls)")
    print("  - task_status, get_push_data  (status queries)")
    print("  - is_connected  (check connection status)")
    print("\nType method names with parameters (e.g., goto target_id=LM2)")
    print("Type 'exit' or 'quit' to exit")
    print("-"*60)
    
    # Import parse_command_line from util
    try:
        from seer_control.util import parse_command_line
    except ImportError:
        # Fallback simple parser
        def parse_command_line(line):
            """Simple command line parser fallback."""
            parts = line.split()
            if not parts:
                return None, {}
            func_name = parts[0]
            params = {}
            for part in parts[1:]:
                if '=' in part:
                    key, val = part.split('=', 1)
                    # Type conversion
                    if val.lower() == 'true':
                        val = True
                    elif val.lower() == 'false':
                        val = False
                    elif val.isdigit():
                        val = int(val)
                    else:
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                    params[key] = val
            return func_name, params
    
    try:
        while True:
            try:
                # Get user input
                line = input("\n🌐 > ").strip()
            except EOFError:
                print()
                break
            
            if not line:
                continue
            
            # Parse command
            func_name, params = parse_command_line(line)
            
            if func_name is None:
                continue
            
            # Handle special commands
            try:
                if func_name in ['exit', 'quit', 'q']:
                    print("\n👋 Exiting...")
                    break
                
                elif func_name == 'help':
                    print("💡 Type any method name with parameters: method_name param1=value1 ...")
                    print("   Navigate: navigate trajectory=<name>, goto_navigate_start trajectory=<name>")
                    print(f"   Trajectories: {', '.join(trajectories)}")
                    print("   Basic: goto target_id=<id>, goto_charge")
                    print("   Task: pause_task, resume_task, cancel_task")
                    print("   Emergency: emergency_stop, emergency_recover")
                    print("   Status: task_status, get_push_data, is_connected")
                    print("   Example: navigate trajectory=looptest")
                    print("   Example: goto_navigate_start trajectory=arm_dock2rack")
                    print("   Example: goto target_id=LM2")
                
                # Special handling for methods that return specific types
                elif func_name == 'task_status':
                    status = controller.task_status()
                    status_map = {
                        0: "NONE", 1: "WAITING", 2: "RUNNING", 3: "SUSPENDED",
                        4: "COMPLETED", 5: "FAILED", 6: "CANCELED"
                    }
                    print(f"📊 Task status: {status} ({status_map.get(status, 'UNKNOWN')})")
                
                elif func_name == 'is_connected':
                    connected = controller.is_connected()
                    print(f"🔌 Connection status: {'✅ Connected' if connected else '❌ Disconnected'}")
                
                elif func_name == 'get_push_data':
                    data = controller.get_push_data()
                    print("📡 Push data:")
                    print(f"   Position: {data.get('current_station', 'N/A')}")
                    print(f"   Battery: {data.get('battery_level', 'N/A')}%")
                    print(f"   Charging: {data.get('charging', False)}")
                    if 'jack' in data and 'jack_state' in data['jack']:
                        jack_state_map = {
                            0x00: "Rising", 0x01: "Raised", 0x02: "Lowering",
                            0x03: "Lowered", 0x04: "Stopped", 0xFF: "Failed"
                        }
                        jack_state = data['jack']['jack_state']
                        print(f"   Jack: {jack_state_map.get(jack_state, 'Unknown')}")
                
                elif func_name == 'get_trajectories':
                    trajectories = controller.get_trajectories(force_refresh=params.get('force_refresh', False))
                    print(f"📋 Available trajectories ({len(trajectories)}):")
                    for traj in trajectories:
                        print(f"   - {traj}")
                
                # Try to call the method if it exists
                elif hasattr(controller, func_name):
                    method = getattr(controller, func_name)
                    if callable(method):
                        try:
                            result = method(**params)
                            # Pretty print result
                            if isinstance(result, dict):
                                if result.get('success', False):
                                    print(f"✅ {result.get('message', 'Success')}")
                                    if 'task_id' in result:
                                        print(f"📋 Task ID: {result['task_id']}")
                                else:
                                    print(f"❌ {result.get('message', 'Failed')}")
                            else:
                                print(f"📋 Result: {result}")
                        except TypeError as e:
                            print(f"❌ Invalid parameters for {func_name}: {e}")
                            print(f"   Try: {func_name} with key=value parameters")
                    else:
                        print(f"❌ '{func_name}' is not a callable method")
                
                else:
                    print(f"❌ Unknown command: {func_name}")
                    print("   Type 'help' for available commands")
            
            except ValueError as e:
                print(f"❌ Invalid parameter: {e}")
            except Exception as e:
                print(f"❌ Error executing command: {e}")
                import traceback
                traceback.print_exc()
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    
    finally:
        print("\n" + "="*60)
        print("✅ Session ended")
        print("="*60)


if __name__ == "__main__":
    main()

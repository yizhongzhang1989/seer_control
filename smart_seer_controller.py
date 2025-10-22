#!/usr/bin/env python3
"""
Smart SEER Controller - Generic Robot Control Wrapper

This module provides a reusable controller class for basic SEER robot operations.
It wraps the SeerController with commonly used functions that are not project-specific.
All projects can use this class to provide standardized basic control of SEER robots.

Author: Assistant
Date: October 22, 2025
"""

from seer_control import SeerController
from typing import Optional, Dict, Any, List
import time
import threading
from datetime import datetime


class SmartSeerController:
    """
    Smart SEER Controller - A high-level wrapper for basic robot operations.
    
    This class provides a clean interface for common robot control operations
    including connection management and status queries. It is designed to be
    project-agnostic and reusable across different SEER robot applications.
    
    Attributes:
        robot: The underlying SeerController instance
        robot_ip: IP address of the robot
        is_connected: Connection status flag
        
    Examples:
        # Basic usage
        controller = SmartSeerController("192.168.1.123")
        if controller.connect():
            controller.goto("LM2")
            controller.disconnect()
        
        # Using context manager
        with SmartSeerController("192.168.1.123") as controller:
            if controller.is_connected:
                controller.goto("LM5")
    """
    
    def __init__(
        self, 
        robot_ip: str,
    ):
        """
        Initialize the Smart SEER Controller.
        
        Args:
            robot_ip: IP address of the SEER robot (e.g., "192.168.1.123")
        """
        # Connection settings
        self.robot_ip = robot_ip
        
        # Push configuration
        self.push_interval = 1000  # milliseconds, 0 to disable
        self.push_fields = [
            "x", "y", "angle", "current_station",
            "vx", "vy", "w",
            "battery_level", "charging",
            "emergency", "soft_emc", "fatals", "errors", "warnings", "notices",
            "create_on", "confidence",
            "task_status", "task_type",
            "jack"
        ]
        self._push_data: Dict[str, Any] = {}
        self._push_data_lock = threading.Lock()
        
        # Internal state
        self.robot: Optional[SeerController] = None
        self._is_connected = False
        self._task_id_counter = 0
        self.last_navigation_time: Optional[float] = None  # Timestamp of last navigation call (time.time())
    
    def connect(self, verbose: bool = True) -> bool:
        """
        Connect to the SEER robot.
        
        Establishes connections to all robot services including status, task,
        control interfaces, and push controller (if push_interval > 0).
        
        Args:
            verbose: If True, prints connection status messages (default: True)
            
        Returns:
            True if connected successfully to at least one service, False otherwise
            
        Examples:
            controller = SmartSeerController("192.168.1.123")
            if controller.connect():
                print("Connected!")
            
            # Silent connection
            controller.connect(verbose=False)
        """
        if verbose:
            print(f"\n🔌 Connecting to robot at {self.robot_ip}...")
        
        try:
            self.robot = SeerController(self.robot_ip)
            connections = self.robot.connect_all()
            
            if verbose:
                print("\n📊 Connection Status:")
                for service, connected in connections.items():
                    status_icon = "✅" if connected else "❌"
                    status_text = 'Connected' if connected else 'Disconnected'
                    print(f"  {status_icon} {service}: {status_text}")
            
            # Check if at least one service is connected
            self.is_connected = any(connections.values())
            
            if self.is_connected:
                # Enable push controller if push_interval > 0
                if self.push_interval > 0 and connections.get('push', False):
                    if verbose:
                        print(f"\n⚡ Configuring push controller (interval: {self.push_interval}ms)...")
                    
                    result = self.robot.push.configure_push(
                        interval=self.push_interval,
                        included_fields=self.push_fields
                    )
                    
                    if result and result.get('ret_code') == 0:
                        if verbose:
                            print("   ✅ Push configured successfully")
                        
                        # Start listening with callback
                        if verbose:
                            print("   🎧 Starting push listener...")
                        
                        if self.robot.push.start_listening(callback=self._push_data_callback):
                            if verbose:
                                print("   ✅ Push listener started")
                        else:
                            if verbose:
                                print("   ⚠️  Failed to start push listener")
                    else:
                        if verbose:
                            print("   ⚠️  Push configuration failed")
                
                if verbose:
                    print("\n✅ Connected successfully!")
                return True
            else:
                if verbose:
                    print("\n❌ Failed to connect to any services")
                self.robot = None
                return False
                
        except Exception as e:
            if verbose:
                print(f"\n❌ Connection error: {e}")
            self.robot = None
            self.is_connected = False
            return False
    
    def disconnect(self, verbose: bool = True) -> bool:
        """
        Disconnect from the SEER robot.
        
        Closes all connections to robot services and cleans up resources.
        
        Args:
            verbose: If True, prints disconnection status messages (default: True)
            
        Returns:
            True if disconnected successfully, False if not connected
            
        Examples:
            controller.disconnect()
            
            # Silent disconnection
            controller.disconnect(verbose=False)
        """
        if self.robot is None:
            if verbose:
                print("⚠️  Not connected to any robot")
            return False
        
        try:
            if verbose:
                print("\n🔌 Disconnecting from robot...")
            
            # Stop push listener if running
            if hasattr(self.robot, 'push') and self.robot.push.listening:
                self.robot.push.stop_listening()
            
            self.robot.disconnect_all()
            self.robot = None
            self.is_connected = False
            
            if verbose:
                print("✅ Disconnected successfully")
            return True
            
        except Exception as e:
            if verbose:
                print(f"❌ Disconnection error: {e}")
            return False
    
    def _push_data_callback(self, data: Dict[str, Any]) -> None:
        """
        Callback function for push data (thread-safe).
        
        This is called by the push controller in a background thread.
        Updates the internal push data storage in a thread-safe manner.
        
        Args:
            data: Push data dictionary received from robot
        """
        with self._push_data_lock:
            self._push_data = data.copy()
    
    def __enter__(self):
        """Context manager entry - connects to robot."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnects from robot."""
        self.disconnect()
        return False
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def gen_move_task_list_description(self, move_task_list: List[Dict[str, Any]]) -> str:
        """
        Generate a human-readable description from a move task list.
        
        Extracts station/point IDs and operations to create a concise description
        of the navigation path. Handles various task formats flexibly.
        
        Args:
            move_task_list: List of waypoints/tasks
            
        Returns:
            String description like "LM2 → LM9 → LM5" or "LM9 → AP8 (load) → LM9"
            
        Examples:
            >>> tasks = [{"source_id": "LM2", "id": "LM9"}, {"source_id": "LM9", "id": "LM5"}]
            >>> controller.gen_move_task_list_description(tasks)
            'LM2 → LM9 → LM5'
            
            >>> tasks = [{"source_id": "LM9", "id": "AP8", "operation": "JackLoad"}]
            >>> controller.gen_move_task_list_description(tasks)
            'LM9 → AP8 (load)'
        """
        if not move_task_list:
            return "Empty task list"
        
        path_parts = []
        previous_id = None
        
        for task in move_task_list:
            # Get source and destination
            source_id = task.get('source_id', '')
            dest_id = task.get('id', '')
            operation = task.get('operation', '')
            
            # Skip SELF_POSITION entries in the path
            if source_id == 'SELF_POSITION' and dest_id == 'SELF_POSITION':
                continue
            
            # Add source to path if it's the first or different from previous
            if source_id and source_id != 'SELF_POSITION' and source_id != previous_id:
                path_parts.append(source_id)
                previous_id = source_id
            
            # Add destination to path
            if dest_id and dest_id != 'SELF_POSITION':
                # Add operation annotation if present
                if operation:
                    # Simplify operation name (e.g., "JackLoad" -> "load")
                    op_name = operation.replace('Jack', '').lower()
                    path_parts.append(f"{dest_id} ({op_name})")
                else:
                    path_parts.append(dest_id)
                previous_id = dest_id
        
        # Join with arrow symbol
        if path_parts:
            return ' → '.join(path_parts)
        else:
            return "Navigation task"
    
    def _task_id_gen(self) -> str:
        """
        Generate a unique task ID.
        
        Format: YYYYMMDDHHMMSS_N
        Where N is an incrementing counter that resets each time the controller is created.
        
        Returns:
            Unique task ID string
        """
        self._task_id_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{timestamp}_{self._task_id_counter}"
    
    def get_idle_time(self) -> Optional[float]:
        """
        Get the idle time since last navigation call.
        
        Calculates the time elapsed since the last navigation method was called.
        This is useful for tracking robot idle time and scheduling decisions.
        
        Returns:
            Time in seconds since last navigation call, or None if no navigation has been called yet
            
        Examples:
            # Check idle time
            idle_seconds = controller.get_idle_time()
            if idle_seconds is not None:
                print(f"Robot has been idle for {idle_seconds:.1f} seconds")
                
                # Check if idle for more than 5 minutes
                if idle_seconds > 300:
                    print("Robot idle for more than 5 minutes")
        """
        if self.last_navigation_time is None:
            return None
        return time.time() - self.last_navigation_time
    
    def get_push_data(self) -> Dict[str, Any]:
        """
        Get the latest push data (thread-safe).
        
        Returns a copy of the most recent push data received from the robot.
        This method is thread-safe and can be called from any thread.
        
        Returns:
            Dictionary containing the latest push data, or empty dict if no data received yet
            
        Examples:
            # Get latest push data
            data = controller.get_push_data()
            print(f"Position: ({data.get('x')}, {data.get('y')})")
            print(f"Battery: {data.get('battery_level')}%")
        """
        with self._push_data_lock:
            return self._push_data.copy()
    
    def print_push_data(self) -> bool:
        """
        Print the current push data in a formatted way.
        
        Displays the latest push data received from the robot in a nicely
        formatted console output. This is useful for debugging and monitoring.
        
        Returns:
            True if push data was printed, False if no data available yet
            
        Examples:
            controller.print_push_data()
        """
        data = self.get_push_data()
        
        if not data:
            print("⚠️  No push data received yet")
            return False
        
        print("\n" + "="*60)
        print("📡 Push Data")
        print("="*60)
        
        # Position data
        if any(k in data for k in ['x', 'y', 'angle', 'current_station']):
            print("\n📍 Position:")
            if 'x' in data:
                print(f"  X: {data['x']:.3f} m")
            if 'y' in data:
                print(f"  Y: {data['y']:.3f} m")
            if 'angle' in data:
                print(f"  Angle: {data['angle']:.3f} rad")
            if 'current_station' in data:
                print(f"  Station: {data['current_station']}")
            if 'confidence' in data:
                print(f"  Confidence: {data['confidence']:.2f}")
        
        # Velocity data
        if any(k in data for k in ['vx', 'vy', 'w']):
            print("\n🏃 Velocity:")
            if 'vx' in data:
                print(f"  Vx: {data['vx']:.3f} m/s")
            if 'vy' in data:
                print(f"  Vy: {data['vy']:.3f} m/s")
            if 'w' in data:
                print(f"  W: {data['w']:.3f} rad/s")
        
        # Battery data
        if any(k in data for k in ['battery_level', 'charging']):
            print("\n🔋 Battery:")
            if 'battery_level' in data:
                print(f"  Level: {data['battery_level']}%")
            if 'charging' in data:
                print(f"  Charging: {'Yes' if data['charging'] else 'No'}")
        
        # Status indicators
        if any(k in data for k in ['emergency', 'fatals', 'errors', 'warnings', 'notices']):
            print("\n⚠️  Status:")
            if 'emergency' in data:
                status_text = "EMERGENCY" if data['emergency'] else "Normal"
                icon = "🚨" if data['emergency'] else "✅"
                print(f"  {icon} Emergency: {status_text}")
            if 'fatals' in data:
                print(f"  Fatals: {data['fatals']}")
            if 'errors' in data:
                print(f"  Errors: {data['errors']}")
            if 'warnings' in data:
                print(f"  Warnings: {data['warnings']}")
            if 'notices' in data:
                print(f"  Notices: {data['notices']}")
        
        # Task data
        if any(k in data for k in ['task_status', 'task_type']):
            print("\n📊 Task:")
            if 'task_status' in data:
                status_map = {
                    0: "NONE", 1: "WAITING", 2: "RUNNING", 3: "SUSPENDED",
                    4: "COMPLETED", 5: "FAILED", 6: "CANCELED"
                }
                status_text = status_map.get(data['task_status'], "UNKNOWN")
                print(f"  Status: {status_text} ({data['task_status']})")
            if 'task_type' in data:
                print(f"  Type: {data['task_type']}")
        
        # Timestamp
        if 'create_on' in data:
            print(f"\n🕐 Timestamp: {data['create_on']}")
        
        print("="*60)
        return True

    # ========================================================================
    # General Navigation Methods
    # ========================================================================
    
    def task_status(self) -> int:
        """
        Query the status of the current running task.
        
        This method is useful for non-blocking workflows where you start a task
        and then periodically check its status until completion.
        
        Returns:
            Task status code:
            - 0: NONE (no task)
            - 1: WAITING
            - 2: RUNNING
            - 3: SUSPENDED
            - 4: COMPLETED
            - 5: FAILED
            - 6: CANCELED
            - -1: Error (robot not connected or query failed)
            
        Examples:
            # Start a non-blocking task
            result = controller.execute_navigation(task_list, "My Task", wait=False)
            
            # Check status periodically
            while True:
                status = controller.task_status()
                if status in [4, 5, 6]:  # COMPLETED, FAILED, or CANCELED
                    break
                time.sleep(1)
        """
        if not self.is_connected or self.robot is None:
            return -1
        
        # Query task status
        result = self.robot.status.query_status('task')
        
        if not result or result.get('ret_code') != 0:
            return -1
        
        return result.get('task_status', -1)

    def goto(self, target_id: str, wait: bool = True, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Simple navigation to a target point - Navigate robot to target by ID.
        
        This is a simplified method that navigates the robot from its current
        position to a specified target station/point. It first checks if the robot
        is already at the target location and skips navigation if so.
        
        Args:
            target_id: Target station/point name (e.g., "LM2", "AP1", "Station5")
            wait: If True, waits for navigation completion (blocking). If False, returns immediately after starting (non-blocking).
            timeout: Maximum time to wait for navigation completion in seconds (default: 60.0, only used if wait=True)
            
        Returns:
            Dictionary with:
            - success (bool): True if already at target or navigation started/completed successfully
            - task_id (str): Task ID assigned by robot (None if already at target or failed)
            - blocking (bool): Whether method waited for completion
            - already_at_target (bool): Whether robot was already at target location
            
        Examples:
            # Blocking navigation (default)
            result = controller.goto("LM2")
            if result["success"]:
                print("Navigation completed!")
            
            # Non-blocking navigation
            result = controller.goto("AP1", wait=False)
            task_id = result["task_id"]
            # Check status later with task_status()
            
            # Custom timeout
            result = controller.goto("LM2", timeout=120.0)
        """
        if not self.is_connected or self.robot is None:
            print("❌ Robot not connected!")
            return {"success": False, "task_id": None, "blocking": wait, "already_at_target": False}
        
        # Record navigation call time
        self.last_navigation_time = time.time()
        
        # Query current location first
        loc_result = self.robot.status.query_status("loc")
        
        if not loc_result or loc_result.get('ret_code') != 0:
            print("⚠️  Warning: Could not query current location, proceeding with navigation...")
            current_station = None
        else:
            current_station = loc_result.get('current_station', '')
            print(f"📍 Current location: {current_station}")
        
        # Check if already at target
        if current_station and current_station == target_id:
            print(f"✅ Already at {target_id}, skipping navigation\n")
            return {"success": True, "task_id": None, "blocking": wait, "already_at_target": True}
        
        print(f"🎯 Navigating to: {target_id}")
        
        # Use gotarget with only the target ID
        result = self.robot.task.gotarget(id=target_id)
        
        if not result or result.get('ret_code') != 0:
            print("❌ Failed to start navigation")
            if result:
                print(f"   Error code: {result.get('ret_code')}")
                print(f"   Message: {result.get('msg', 'No error message')}")
            return {"success": False, "task_id": None, "blocking": wait, "already_at_target": False}
        
        task_id = result.get('task_id', 'N/A')
        print(f"✅ Navigation started (ID: {task_id})")
        
        # If non-blocking mode, return immediately
        if not wait:
            print("🔓 Non-blocking mode: returning immediately (navigation running in background)\n")
            return {"success": True, "task_id": task_id, "blocking": False, "already_at_target": False}
        
        # Blocking mode: wait for completion
        print(f"⏳ Waiting for completion (timeout: {timeout}s)...")
        
        # Wait for task completion
        wait_result = self.robot.wait_task_complete(query_interval=1.0, timeout=timeout)
        
        # Display result
        print(f"\n📊 Result: {wait_result['status_text']} in {wait_result['elapsed_time']:.1f}s")
        
        if wait_result['finished_path']:
            print(f"   Path: {' → '.join(wait_result['finished_path'])}")
        
        if wait_result['success']:
            print(f"✅ Arrived at {target_id}!\n")
            return {"success": True, "task_id": task_id, "blocking": True, "already_at_target": False}
        else:
            print(f"❌ Navigation to {target_id} failed: {wait_result['status_text']}\n")
            return {"success": False, "task_id": task_id, "blocking": True, "already_at_target": False}

    def execute_navigation(self, move_task_list: List[Dict[str, Any]], wait: bool = True, timeout: float = 600.0) -> Dict[str, Any]:
        """
        Execute a navigation task with a given move task list.
        
        This is a generic method that handles the common pattern for all navigation tasks:
        1. Check robot connection
        2. Send gotargetlist command
        3. Optionally wait for task completion
        4. Report results
        
        Args:
            move_task_list: List of waypoints/tasks to execute
            wait: If True, waits for task completion (blocking). If False, returns immediately after starting task (non-blocking).
            timeout: Maximum time to wait for task completion in seconds (default: 600.0, only used if wait=True)
            
        Returns:
            Dictionary with:
            - success (bool): True if task started/completed successfully
            - task_id (str): Task ID assigned by robot
            - blocking (bool): Whether method waited for completion
            - result (dict): Full result from wait_task_complete if wait=True, otherwise None
        """
        if not self.is_connected or self.robot is None:
            print("❌ Robot not connected!")
            return {"success": False, "task_id": None, "blocking": wait, "result": None}
        
        # Record navigation call time
        self.last_navigation_time = time.time()
        
        # Auto-generate description from task list
        description = self.gen_move_task_list_description(move_task_list)
        
        print(f"\n🚀 {description}")
        
        # Send gotargetlist command
        result = self.robot.task.gotargetlist(move_task_list)
        
        if not result or result.get('ret_code') != 0:
            print("❌ Failed to start task")
            if result:
                print(f"   Error code: {result.get('ret_code')}")
                print(f"   Message: {result.get('msg', 'No error message')}")
            return {"success": False, "task_id": None, "blocking": wait, "result": result}
        
        task_id = result.get('task_id', 'N/A')
        print(f"✅ Task started (ID: {task_id})")
        
        # If non-blocking mode, return immediately
        if not wait:
            print("🔓 Non-blocking mode: returning immediately (task running in background)\n")
            return {"success": True, "task_id": task_id, "blocking": False, "result": result}
        
        # Blocking mode: wait for completion
        print(f"⏳ Waiting for completion (timeout: {timeout}s)...")
        
        # Wait for task completion
        wait_result = self.robot.wait_task_complete(query_interval=1.0, timeout=timeout)
        
        # Display result
        print(f"\n📊 Result: {wait_result['status_text']} in {wait_result['elapsed_time']:.1f}s")
        
        if wait_result['finished_path']:
            print(f"   Path: {' → '.join(wait_result['finished_path'])}")
        
        if wait_result['success']:
            print(f"✅ {description} completed successfully!\n")
            return {"success": True, "task_id": task_id, "blocking": True, "result": wait_result}
        else:
            print(f"❌ {description} failed: {wait_result['status_text']}\n")
            return {"success": False, "task_id": task_id, "blocking": True, "result": wait_result}
        
    def goto_start(self, move_task_list: List[Dict[str, Any]], wait: bool = True, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Navigate to the starting position of a move task list.
        
        This method finds the first source_id in the move_task_list that is not
        "SELF_POSITION" and navigates the robot there. This is useful for positioning
        the robot at the correct starting location before executing a task sequence.
        
        Args:
            move_task_list: List of waypoints/tasks (same format as execute_navigation)
            wait: If True, waits for navigation completion (blocking). If False, returns immediately after starting (non-blocking).
            timeout: Maximum time to wait for navigation completion in seconds (default: 60.0, only used if wait=True)
            
        Returns:
            Dictionary with:
            - success (bool): True if navigation to start position completed/started successfully
            - task_id (str): Task ID assigned by robot
            - blocking (bool): Whether method waited for completion
            - start_position (str): The identified start position (None if not found)
            
        Examples:
            # Blocking (default)
            move_task_list = [
                {"source_id": "LM9", "id": "AP8", "task_id": "001", "operation": "JackLoad"},
                {"source_id": "AP8", "id": "LM9", "task_id": "002"},
                ...
            ]
            result = controller.goto_start(move_task_list)  # Will navigate to LM9 and wait
            
            # Non-blocking
            result = controller.goto_start(move_task_list, wait=False)  # Starts navigation to LM9, returns immediately
            
            # Custom timeout
            result = controller.goto_start(move_task_list, timeout=120.0)
        """
        if not self.is_connected or self.robot is None:
            print("❌ Robot not connected!")
            return {"success": False, "task_id": None, "blocking": wait, "start_position": None}
        
        if not move_task_list:
            print("❌ Empty move task list!")
            return {"success": False, "task_id": None, "blocking": wait, "start_position": None}
        
        # Find the first source_id that is not SELF_POSITION
        start_position = None
        for task in move_task_list:
            source_id = task.get('source_id', '')
            if source_id and source_id != 'SELF_POSITION':
                start_position = source_id
                break
        
        if not start_position:
            print("⚠️ No valid starting position found in move task list (all are SELF_POSITION)")
            return {"success": False, "task_id": None, "blocking": wait, "start_position": None}
        
        print(f"📍 Starting position identified: {start_position}")
        result = self.goto(start_position, wait=wait, timeout=timeout)
        result["start_position"] = start_position
        return result
    
    def goto_charge(self, via_point: str = "LM2", charge_point: str = "CP0", wait: bool = True, timeout: float = 300.0) -> Dict[str, Any]:
        """
        Navigate robot to charging point.
        First checks if already charging. If not charging, goes via intermediate point to charge point.
        
        Args:
            via_point: Intermediate waypoint before charging (default: "LM2")
            charge_point: Charging station ID (default: "CP0")
            wait: If True, waits for navigation completion (blocking). If False, returns immediately after starting (non-blocking).
            timeout: Maximum time to wait for each navigation segment in seconds (default: 300.0, only used if wait=True)
        
        Returns:
            Dictionary with success status and task information
            
        Examples:
            # Use default charging route (via LM2 to CP0)
            result = controller.goto_charge()
            
            # Custom charging route
            result = controller.goto_charge(via_point="LM5", charge_point="CP1")
            
            # Non-blocking
            result = controller.goto_charge(wait=False)
            
            # Custom timeout
            result = controller.goto_charge(timeout=600.0)
        """
        if not self.is_connected or self.robot is None:
            print("❌ Robot not connected!")
            return {"success": False, "task_id": None, "blocking": wait}
        
        # Check battery status to see if already charging
        print("🔋 Checking charging status...")
        battery_result = self.robot.status.query_status("battery")
        
        if not battery_result or battery_result.get('ret_code') != 0:
            print("⚠️  Warning: Could not query battery status, proceeding with navigation...")
            is_charging = False
        else:
            is_charging = battery_result.get('charging', False)
            battery_level = battery_result.get('battery_level', 'N/A')
            print(f"   Battery: {battery_level}%, Charging: {is_charging}")
        
        # If already charging, no need to move
        if is_charging:
            print("✅ Already charging, no navigation needed\n")
            return {"success": True, "task_id": None, "blocking": wait, "already_charging": True}
        
        # Not charging, go via intermediate point to charge point
        print(f"📍 Not charging, navigating: {via_point} → {charge_point}")
        
        # First go to intermediate point
        result = self.goto(via_point, wait=wait, timeout=timeout)
        if not result["success"]:
            print(f"❌ Failed to reach {via_point}")
            return result
        
        # Then go to charge point
        result = self.goto(charge_point, wait=wait, timeout=timeout)
        return result


# ============================================================================
# Command Line Interface
# ============================================================================

def main():
    """
    Main interactive loop for SmartSeerController.
    
    Provides a command-line interface for controlling the SEER robot
    with navigation functions similar to dc_demo_2025.py.
    """
    print("="*60)
    print("🤖 Smart SEER Controller - Interactive Control")
    print("="*60)
    
    # Set robot IP directly
    robot_ip = "192.168.1.123"
    
    # Auto-connect at start
    print("\n🔌 Connecting to robot...")
    controller = SmartSeerController(robot_ip)
    if not controller.connect():
        print("❌ Failed to connect. Exiting.")
        return
    
    print("\nType method names with parameters (e.g., goto target_id=LM2)")
    print("Type 'exit' or 'quit' to exit")
    print("-"*60)
    
    # Import parse_command_line from util
    try:
        from seer_control.util import parse_command_line
    except ImportError:
        # Fallback simple parser if util not available
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
                line = input("\n🤖 > ").strip()
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
                    print("   Available methods: goto, goto_charge, goto_start, execute_navigation, task_status")
                    print("   Example: goto target_id=LM2")
                
                # Special handling for task_status - print the status code
                elif func_name == 'task_status':
                    status = controller.task_status()
                    print(f"📊 Task status: {status}")
                
                # Try to call the method directly if it exists
                elif hasattr(controller, func_name):
                    method = getattr(controller, func_name)
                    if callable(method):
                        try:
                            result = method(**params)
                            # If result is a dict (for navigation functions), show task_id
                            if isinstance(result, dict) and 'task_id' in result:
                                print(f"📋 Task ID: {result.get('task_id', 'N/A')}")
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
        # Auto-disconnect at end
        if controller.is_connected:
            print("\n🔌 Disconnecting from robot...")
            controller.disconnect()
        
        print("\n" + "="*60)
        print("✅ Session ended")
        print("="*60)


if __name__ == "__main__":
    main()

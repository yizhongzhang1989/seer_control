#!/usr/bin/env python3
"""
DC Demo 2025 Controller - Project-Specific Robot Control

This module provides a specialized controller class for DC Demo 2025 project.
It inherits from SmartSeerController and adds DC-specific navigation functions
for arm and courier movements.

Author: Assistant
Date: October 22, 2025
"""

from smart_seer_controller import SmartSeerController
from typing import Dict, Any, List


class DCDemo2025Controller(SmartSeerController):
    """
    DC Demo 2025 Controller - Project-specific wrapper for DC robot operations.
    
    This class extends SmartSeerController with navigation functions specific to
    the DC Demo 2025 project. It provides a unified navigate() method that
    executes predefined trajectories:
    - looptest: Loop test navigation
    - arm_dock2rack, arm_rack2side, arm_side2rack, arm_rack2dock: Arm movements
    - courier_dock2rack, courier_rack2dock: Courier movements
    
    Inherits all base functionality from SmartSeerController including:
    - Connection management (connect/disconnect)
    - Status queries
    - Basic navigation (goto, goto_start, goto_charge)
    - Push data monitoring
    - Idle time tracking
    
    Examples:
        # Basic usage
        controller = DCDemo2025Controller("192.168.1.123")
        if controller.connect():
            # Use base methods
            controller.print_status()
            
            # Use DC-specific navigation with trajectory names
            controller.navigate("looptest")
            controller.navigate("arm_dock2rack", wait=False)
            
            # Check available trajectories
            print(list(controller.move_task_list.keys()))
            
            controller.disconnect()
    """
    
    def __init__(self, robot_ip: str):
        """
        Initialize the DC Demo 2025 Controller.
        
        Args:
            robot_ip: IP address of the SEER robot (e.g., "192.168.1.123")
        """
        super().__init__(robot_ip)
        
        # Define all move task lists for DC-specific navigation
        self.move_task_list = {
            "smalltest": [
                {
                    "source_id": "LM2",
                    "id": "LM9",
                    "task_id": None  # Will be set dynamically
                },
                {
                    "source_id": "LM9",
                    "id": "LM2",
                    "task_id": None
                }
            ],
            "looptest": [
                {
                    "id": "LM9",
                    "source_id": "LM2",
                    "task_id": None  # Will be set dynamically
                },
                {
                    "id": "LM5",
                    "source_id": "LM9",
                    "task_id": None
                },
                {
                    "id": "LM2",
                    "source_id": "LM5",
                    "task_id": None
                }
            ],
            "arm_dock2rack": [
                {
                    "source_id": "LM9",
                    "id": "AP8",
                    "task_id": None,
                    "recognize": True,
                    "operation": "JackLoad"
                },
                {
                    "source_id": "AP8",
                    "id": "LM9",
                    "task_id": None,
                },
                {
                    "source_id": "LM9",
                    "id": "LM5",
                    "task_id": None,
                    "spin": True,
                },
                {
                    "source_id": "LM5",
                    "id": "AP10",
                    "task_id": None,
                    "spin": True,
                    "operation": "JackUnload"
                },
            ],
            "arm_rack2side": [
                {
                    "source_id": "SELF_POSITION",
                    "id": "SELF_POSITION",
                    "task_id": None,
                    "operation": "JackLoad",
                    "spin": True,
                },
                {
                    "source_id": "AP10",
                    "id": "LM12",
                    "task_id": None,
                    "spin": True,
                },
                {
                    "source_id": "LM12",
                    "id": "AP11",
                    "task_id": None,
                    "operation": "JackUnload"
                },
                {
                    "source_id": "AP11",
                    "id": "LM13",
                    "task_id": None,
                },
                {
                    "source_id": "LM13",
                    "id": "LM2",
                    "task_id": None,
                },
            ],
            "arm_side2rack": [
                {
                    "source_id": "LM2",
                    "id": "LM13",
                    "task_id": None,
                },
                {
                    "source_id": "LM13",
                    "id": "AP11",
                    "task_id": None,
                    "recognize": True,
                },
                {
                    "source_id": "SELF_POSITION",
                    "id": "SELF_POSITION",
                    "task_id": None,
                    "move_angle": 1.5707963,
                    "skill_name": "GoByOdometer",
                    "speed_w": 0.5,
                    "loc_mode": 1,
                    "operation": "JackLoad",
                },
                {
                    "source_id": "SELF_POSITION",
                    "id": "SELF_POSITION",
                    "task_id": None,
                    "operation": "JackLoad",
                },
                {
                    "source_id": "AP11",
                    "id": "LM12",
                    "task_id": None,
                },
                {
                    "source_id": "SELF_POSITION",
                    "id": "SELF_POSITION",
                    "task_id": None,
                    "move_angle": 1.5707963,
                    "skill_name": "GoByOdometer",
                    "speed_w": 0.5,
                    "loc_mode": 1,
                },
                {
                    "source_id": "LM12",
                    "id": "AP10",
                    "task_id": None,
                    "spin": True,
                    "operation": "JackUnload"
                },
            ],
            "arm_rack2dock": [
                {
                    "source_id": "SELF_POSITION",
                    "id": "SELF_POSITION",
                    "task_id": None,
                    "operation": "JackLoad",
                },
                {
                    "source_id": "AP10",
                    "id": "LM5",
                    "task_id": None,
                    "spin": True,
                },
                {
                    "source_id": "LM5",
                    "id": "LM9",
                    "task_id": None,
                    "spin": True,
                },
                {
                    "source_id": "LM9",
                    "id": "AP8",
                    "task_id": None,
                    "operation": "JackUnload"
                },
                {           
                    "source_id": "AP8",
                    "id": "LM9",
                    "task_id": None,
                }
            ],
            "courier_dock2rack": [
                {
                    "source_id": "LM4",
                    "id": "AP3",
                    "task_id": None,
                    "recognize": True,
                    "operation": "JackLoad"
                },
                {
                    "source_id": "AP3",
                    "id": "LM4",
                    "task_id": None,
                },
                {
                    "source_id": "SELF_POSITION",
                    "id": "SELF_POSITION",
                    "task_id": None,
                    "move_angle": 1.5707963,
                    "skill_name": "GoByOdometer",
                    "speed_w": 0.5,
                    "loc_mode": 1,
                },
                {
                    "source_id": "LM4",
                    "id": "LM5",
                    "task_id": None,
                    "spin": True
                },
                {
                    "source_id": "LM5",
                    "id": "AP7",
                    "task_id": None,
                    "operation": "JackUnload",
                    "spin": True
                }
            ],
            "courier_rack2dock": [
                {
                    "source_id": "SELF_POSITION",
                    "id": "SELF_POSITION",
                    "task_id": None,
                    "operation": "JackLoad",
                },
                {
                    "source_id": "AP7",
                    "id": "LM5",
                    "task_id": None,
                    "spin": True
                },
                {
                    "source_id": "LM5",
                    "id": "LM4",
                    "task_id": None,
                    "spin": True
                },
                {
                    "source_id": "LM4",
                    "id": "AP3",
                    "task_id": None,
                    "operation": "JackUnload"
                },
                {
                    "source_id": "AP3",
                    "id": "LM4",
                    "task_id": None,
                }
            ]
        }
    
    def _prepare_task_list(self, task_name: str) -> List[Dict[str, Any]]:
        """
        Prepare a task list by creating a deep copy and setting task IDs.
        
        Args:
            task_name: Name of the task list to prepare
            
        Returns:
            List of task dictionaries with unique task IDs assigned
        """
        import copy
        task_list = copy.deepcopy(self.move_task_list[task_name])
        for task in task_list:
            task["task_id"] = self._task_id_gen()
        return task_list
    
    # ========================================================================
    # DC-Specific Navigation Functions
    # ========================================================================
    
    def navigate(self, trajectory: str, wait: bool = True, timeout: float = 600.0) -> Dict[str, Any]:
        """
        Execute a navigation task using a predefined trajectory.
        
        This is a unified navigation method that executes any of the predefined
        trajectories defined in self.move_task_list.
        
        Args:
            trajectory: Name of the trajectory to execute. Available trajectories:
                       - "looptest": LM2 → LM9 → LM5 → LM2
                       - "arm_dock2rack": LM9 → AP8 (load) → LM9 → LM5 → AP10 (unload)
                       - "arm_rack2side": AP10 (load) → LM12 → AP11 (unload)
                       - "arm_side2rack": AP11 (load) → LM12 → AP10 (unload)
                       - "arm_rack2dock": AP10 (load) → LM5 → LM9 → AP8 (unload) → LM9
                       - "courier_dock2rack": LM4 → AP3 (load) → LM4 → LM5 → AP7 (unload)
                       - "courier_rack2dock": Self (load) → LM5 → LM4 → AP3 (unload) → LM4
            wait: If True, waits for navigation completion (blocking). If False, returns immediately after starting (non-blocking).
            timeout: Maximum time to wait for task completion in seconds (default: 600.0, only used if wait=True)
        
        Returns:
            Dictionary with success status and task information
            
        Examples:
            # Blocking (default)
            result = controller.navigate("looptest")
            
            # Non-blocking
            result = controller.navigate("arm_dock2rack", wait=False)
            
            # Custom timeout
            result = controller.navigate("courier_dock2rack", timeout=300.0)
            
            # Check available trajectories
            print(list(controller.move_task_list.keys()))
        """
        # Validate trajectory name
        if trajectory not in self.move_task_list:
            print(f"❌ Unknown trajectory: {trajectory}")
            print(f"   Available trajectories: {list(self.move_task_list.keys())}")
            return {"success": False, "task_id": None, "blocking": wait, "result": None}
        
        # Prepare task list and execute navigation
        # Description will be auto-generated from task list by execute_navigation()
        task_list = self._prepare_task_list(trajectory)
        result = self.execute_navigation(task_list, wait=wait, timeout=timeout)
        return result


# ============================================================================
# Command Line Interface
# ============================================================================

def main():
    """
    Main interactive loop for DCDemo2025Controller.
    
    Provides a command-line interface for controlling the SEER robot
    with DC Demo 2025 specific navigation functions.
    """
    print("="*60)
    print("🤖 DC Demo 2025 Controller - Interactive Control")
    print("="*60)
    
    # Set robot IP directly
    robot_ip = "192.168.1.123"
    
    # Auto-connect at start
    print("\n🔌 Connecting to robot...")
    controller = DCDemo2025Controller(robot_ip)
    if not controller.connect():
        print("❌ Failed to connect. Exiting.")
        return
    
    print("\n📝 Available DC-specific commands:")
    print("  - navigate trajectory=<name>  (unified navigation command)")
    print("\n📝 Available trajectories:")
    print("  - looptest, arm_dock2rack, arm_rack2side, arm_side2rack, arm_rack2dock")
    print("  - courier_dock2rack, courier_rack2dock")
    print("\n📝 Available base commands:")
    print("  - goto, goto_charge, goto_start, status, print_status, print_push_data")
    print("  - task_status, get_idle_time, get_push_data")
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
                    print("   DC-specific: navigate trajectory=<name>")
                    print("   Trajectories: looptest, arm_dock2rack, arm_rack2side, arm_side2rack,")
                    print("                 arm_rack2dock, courier_dock2rack, courier_rack2dock")
                    print("   Base methods: goto, goto_charge, goto_start, status, print_status, print_push_data")
                    print("   Example: navigate trajectory=looptest")
                    print("   Example: navigate trajectory=arm_dock2rack wait=false")
                    print("   Example: goto target_id=LM2 timeout=120")
                
                # Special handling for status - use print_status() for formatted output
                elif func_name == 'status':
                    controller.print_status()
                
                # Special handling for task_status - print the status code
                elif func_name == 'task_status':
                    status = controller.task_status()
                    print(f"📊 Task status: {status}")
                
                # Special handling for get_idle_time - print the idle time
                elif func_name == 'get_idle_time':
                    idle_time = controller.get_idle_time()
                    if idle_time is not None:
                        print(f"⏱️  Idle time: {idle_time:.1f} seconds")
                    else:
                        print("⏱️  No navigation called yet")
                
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

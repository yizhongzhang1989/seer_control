#!/usr/bin/env python3
"""
DC Demo 2025 - Interactive Robot Control Script

This script provides an interactive command-line interface for controlling
the SEER robot. The robot controller is initialized as a global variable,
and users can execute various control functions by typing commands.

Each function monitors task completion and only returns when the robot
has completed the requested operation.

Author: Assistant
Date: October 21, 2025
"""

from seer_control import SeerController
import json
import time
from datetime import datetime
from typing import Optional, List, Dict, Any


# ============================================================================
# Global Variables
# ============================================================================

# Global robot controller instance
robot: Optional[SeerController] = None

# Task ID counter for unique task identification
_task_id_counter = 0


# ============================================================================
# Utility Functions
# ============================================================================

def task_id_gen() -> str:
    """
    Generate a unique task ID.
    
    Format: YYYYMMDDHHMMSS_N
    Where N is an incrementing counter that resets each time the script runs.
    
    Returns:
        Unique task ID string
    """
    global _task_id_counter
    _task_id_counter += 1
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{_task_id_counter}"


def connect(ip: str = "192.168.1.123") -> bool:
    """
    Connect to the robot.
    
    Args:
        ip: Robot IP address (default: 192.168.1.123)
        
    Returns:
        True if connected successfully
    """
    global robot
    
    print(f"\n🔌 Connecting to robot at {ip}...")
    
    robot = SeerController(ip)
    connections = robot.connect_essential()
    
    print("\n📊 Connection Status:")
    for service, connected in connections.items():
        status_icon = "✅" if connected else "❌"
        print(f"  {status_icon} {service}: {'Connected' if connected else 'Disconnected'}")
    
    if any(connections.values()):
        print("\n✅ Connected successfully!")
        return True
    else:
        print("\n❌ Failed to connect to any services")
        robot = None
        return False


def disconnect() -> bool:
    """
    Disconnect from the robot.
    
    Returns:
        True if disconnected successfully
    """
    global robot
    
    if robot is None:
        print("⚠️ Not connected to any robot")
        return False
    
    print("\n🔌 Disconnecting from robot...")
    robot.disconnect_all()
    robot = None
    print("✅ Disconnected successfully")
    return True


def status() -> bool:
    """
    Display current robot status.
    
    Returns:
        True if status retrieved successfully
    """
    if robot is None:
        print("❌ Robot not connected! Use 'connect' first.")
        return False
    
    print("\n" + "="*60)
    print("🤖 Robot Status")
    print("="*60)
    
    # Get position
    loc = robot.status.query_status('loc')
    if loc and loc.get('ret_code') == 0:
        print(f"\n📍 Position:")
        print(f"  X: {loc.get('x', 0):.3f} m")
        print(f"  Y: {loc.get('y', 0):.3f} m")
        print(f"  Angle: {loc.get('angle', 0):.3f} rad")
    
    # Get battery
    battery = robot.status.query_status('battery')
    if battery and battery.get('ret_code') == 0:
        print(f"\n🔋 Battery:")
        print(f"  Level: {battery.get('battery', 0)}%")
    
    # Get task status
    task = robot.status.query_status('task')
    if task and task.get('ret_code') == 0:
        task_status = task.get('task_status', -1)
        status_text = {
            0: "NONE", 1: "WAITING", 2: "RUNNING", 3: "SUSPENDED",
            4: "COMPLETED", 5: "FAILED", 6: "CANCELED"
        }.get(task_status, "UNKNOWN")
        print(f"\n📊 Task Status:")
        print(f"  Status: {status_text} ({task_status})")
        if task.get('target_id'):
            print(f"  Target: {task.get('target_id')}")
            print(f"  Distance: {task.get('target_dist', 0):.2f} m")
    
    # Get version
    version = robot.status.query_status('version')
    if version and version.get('ret_code') == 0:
        print(f"\n📦 Version:")
        print(f"  Software: {version.get('software_version', 'N/A')}")
    
    print("="*60)
    return True


# ============================================================================
# Generic Navigation Execution Function
# ============================================================================

def execute_navigation(move_task_list: List[Dict[str, Any]], description: str) -> bool:
    """
    Execute a navigation task with a given move task list.
    
    This is a generic function that handles the common pattern for all navigation tasks:
    1. Check robot connection
    2. Send gotargetlist command
    3. Wait for task completion
    4. Report results
    
    Args:
        move_task_list: List of waypoints/tasks to execute
        description: Human-readable description of the navigation task
        
    Returns:
        True if task completed successfully, False otherwise
    """
    if robot is None:
        print("❌ Robot not connected!")
        return False
    
    print(f"\n🚀 {description}")
    
    # Send gotargetlist command
    result = robot.task.gotargetlist(move_task_list)
    
    if not result or result.get('ret_code') != 0:
        print("❌ Failed to start task")
        if result:
            print(f"   Error code: {result.get('ret_code')}")
            print(f"   Message: {result.get('msg', 'No error message')}")
        return False
    
    print(f"✅ Task started (ID: {result.get('task_id', 'N/A')})")
    print("⏳ Waiting for completion...")
    
    # Wait for task completion
    wait_result = robot.wait_task_complete(query_interval=1.0, timeout=600.0)
    
    # Display result
    print(f"\n📊 Result: {wait_result['status_text']} in {wait_result['elapsed_time']:.1f}s")
    
    if wait_result['finished_path']:
        print(f"   Path: {' → '.join(wait_result['finished_path'])}")
    
    if wait_result['success']:
        print(f"✅ {description} completed successfully!\n")
        return True
    else:
        print(f"❌ {description} failed: {wait_result['status_text']}\n")
        return False


def goto(target_id: str) -> bool:
    """
    Simple navigation to a target point - Navigate robot to target by ID.
    
    This is a simplified function that navigates the robot from its current
    position to a specified target station/point. It first checks if the robot
    is already at the target location and skips navigation if so.
    
    Args:
        target_id: Target station/point name (e.g., "LM2", "AP1", "Station5")
        
    Returns:
        True if already at target or navigation completed successfully, False otherwise
        
    Examples:
        # Navigate to a landmark
        goto("LM2")
        
        # Navigate to an action point
        goto("AP1")
    """
    if robot is None:
        print("❌ Robot not connected!")
        return False
    
    # Query current location first
    loc_result = robot.status.query_status("loc")
    
    if not loc_result or loc_result.get('ret_code') != 0:
        print("⚠️  Warning: Could not query current location, proceeding with navigation...")
        current_station = None
    else:
        current_station = loc_result.get('current_station', '')
        print(f"📍 Current location: {current_station}")
    
    # Check if already at target
    if current_station and current_station == target_id:
        print(f"✅ Already at {target_id}, skipping navigation\n")
        return True
    
    print(f"🎯 Navigating to: {target_id}")
    
    # Use gotarget with only the target ID
    result = robot.task.gotarget(id=target_id)
    
    if not result or result.get('ret_code') != 0:
        print("❌ Failed to start navigation")
        if result:
            print(f"   Error code: {result.get('ret_code')}")
            print(f"   Message: {result.get('msg', 'No error message')}")
        return False
    
    print(f"✅ Navigation started (ID: {result.get('task_id', 'N/A')})")
    print("⏳ Waiting for completion...")
    
    # Wait for task completion
    wait_result = robot.wait_task_complete(query_interval=1.0, timeout=600.0)
    
    # Display result
    print(f"\n📊 Result: {wait_result['status_text']} in {wait_result['elapsed_time']:.1f}s")
    
    if wait_result['finished_path']:
        print(f"   Path: {' → '.join(wait_result['finished_path'])}")
    
    if wait_result['success']:
        print(f"✅ Arrived at {target_id}!\n")
        return True
    else:
        print(f"❌ Navigation to {target_id} failed: {wait_result['status_text']}\n")
        return False


def goto_start(move_task_list: List[Dict[str, Any]]) -> bool:
    """
    Navigate to the starting position of a move task list.
    
    This function finds the first source_id in the move_task_list that is not
    "SELF_POSITION" and navigates the robot there. This is useful for positioning
    the robot at the correct starting location before executing a task sequence.
    
    Args:
        move_task_list: List of waypoints/tasks (same format as execute_navigation)
        
    Returns:
        True if navigation to start position completed successfully, False otherwise
        
    Examples:
        # Navigate to starting position before running arm_dock2rack
        move_task_list = [
            {"source_id": "LM9", "id": "AP8", "task_id": "001", "operation": "JackLoad"},
            {"source_id": "AP8", "id": "LM9", "task_id": "002"},
            ...
        ]
        goto_start(move_task_list)  # Will navigate to LM9
        
        # If first source_id is SELF_POSITION, finds next non-SELF_POSITION
        move_task_list = [
            {"source_id": "SELF_POSITION", "id": "SELF_POSITION", "task_id": "001"},
            {"source_id": "AP10", "id": "LM12", "task_id": "002"},
            ...
        ]
        goto_start(move_task_list)  # Will navigate to AP10
    """
    if robot is None:
        print("❌ Robot not connected!")
        return False
    
    if not move_task_list:
        print("❌ Empty move task list!")
        return False
    
    # Find the first source_id that is not SELF_POSITION
    start_position = None
    for task in move_task_list:
        source_id = task.get('source_id', '')
        if source_id and source_id != 'SELF_POSITION':
            start_position = source_id
            break
    
    if not start_position:
        print("⚠️ No valid starting position found in move task list (all are SELF_POSITION)")
        return False
    
    print(f"📍 Starting position identified: {start_position}")
    return goto(start_position)


# ============================================================================
# Navigation Functions for DC Robot
# ============================================================================

def looptest() -> bool:
    """
    Execute a loop test navigating through multiple stations: LM2 -> LM9 -> LM5 -> LM2.
    
    Returns:
        True if loop test completed successfully
    """
    # Define the move task list: LM2 -> LM9 -> LM5 -> LM2
    move_task_list = [
        {
            "id": "LM9",
            "source_id": "LM2",
            "task_id": task_id_gen()
        },
        {
            "id": "LM5",
            "source_id": "LM9",
            "task_id": task_id_gen()
        },
        {
            "id": "LM2",
            "source_id": "LM5",
            "task_id": task_id_gen()
        }
    ]
    
    # Move to start position
    if not goto_start(move_task_list):
        return False
    
    return execute_navigation(move_task_list, "Loop Test: LM2 → LM9 → LM5 → LM2")


def arm_dock2rack() -> bool:
    """
    Move from dock to rack: LM9 -> AP8 (load) -> LM9 -> LM5 -> AP10 (unload).
    
    Returns:
        True if task completed successfully
    """
    # Define the move task list
    move_task_list = [
        {
            "source_id": "LM9",
            "id": "AP8",
            "task_id": task_id_gen(),
            "recognize": True,
            "operation": "JackLoad"
        },
        {
            "source_id": "AP8",
            "id": "LM9",
            "task_id": task_id_gen(),
        },
        {
            "source_id": "LM9",
            "id": "LM5",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "source_id": "LM5",
            "id": "AP10",
            "task_id": task_id_gen(),
            "spin": True,
            "operation": "JackUnload"
        },
    ]
    
    # Move to start position
    if not goto_start(move_task_list):
        return False
    
    return execute_navigation(move_task_list, "Dock to Rack: LM9 → AP8 (load) → LM9 → LM5 → AP10 (unload)")


def arm_rack2side() -> bool:
    """
    Move from rack to side: AP10 (load) -> LM12 -> AP11 (unload).
    
    Returns:
        True if task completed successfully
    """
    # Define the move task list
    move_task_list = [
        {
            "source_id": "SELF_POSITION",
            "id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "operation": "JackLoad",
            "spin": True,
        },
        {
            "source_id": "AP10",
            "id": "LM12",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "source_id": "LM12",
            "id": "AP11",
            "task_id": task_id_gen(),
            "operation": "JackUnload"
        },
        {
            "source_id": "AP11",
            "id": "LM13",
            "task_id": task_id_gen(),
        },
        {
            "source_id": "LM13",
            "id": "LM2",
            "task_id": task_id_gen(),
        },
    ]
    
    # Move to start position
    if not goto_start(move_task_list):
        return False
    
    return execute_navigation(move_task_list, "Rack to Side: AP10 (load) → LM12 → AP11 (unload)")


def arm_side2rack() -> bool:
    """
    Move from side to rack: AP11 (load) -> LM12 -> AP10 (unload).
    
    Returns:
        True if task completed successfully
    """
    # Define the move task list
    move_task_list = [
        {
            "source_id": "LM2",
            "id": "LM13",
            "task_id": task_id_gen(),
        },
        {
            "source_id": "LM13",
            "id": "AP11",
            "task_id": task_id_gen(),
            "recognize": True,
        },
        {
            "source_id": "SELF_POSITION",
            "id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "move_angle": 1.5707963,
            "skill_name": "GoByOdometer",
            "speed_w": 0.5,
            "loc_mode": 1,
            "operation": "JackLoad",
        },
        {
            "source_id": "SELF_POSITION",
            "id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "operation": "JackLoad",
        },
        {
            "source_id": "AP11",
            "id": "LM12",
            "task_id": task_id_gen(),
        },
        {
            "source_id": "SELF_POSITION",
            "id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "move_angle": 1.5707963,
            "skill_name": "GoByOdometer",
            "speed_w": 0.5,
            "loc_mode": 1,
        },
        {
            "source_id": "LM12",
            "id": "AP10",
            "task_id": task_id_gen(),
            "spin": True,
            "operation": "JackUnload"
        },
    ]
    
    # Move to start position
    if not goto_start(move_task_list):
        return False
    
    return execute_navigation(move_task_list, "Side to Rack: AP11 (load) → LM12 → AP10 (unload)")


def arm_rack2dock() -> bool:
    """
    Move from rack to dock: AP10 (load) -> LM5 -> LM9 -> AP8 (unload) -> LM9.
    
    Returns:
        True if task completed successfully
    """
    # Define the move task list
    move_task_list = [
        {
            "source_id": "SELF_POSITION",
            "id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "operation": "JackLoad",
        },
        {
            "source_id": "AP10",
            "id": "LM5",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "source_id": "LM5",
            "id": "LM9",
            "task_id": task_id_gen(),
            "spin": True,
        },
        {
            "source_id": "LM9",
            "id": "AP8",
            "task_id": task_id_gen(),
            "operation": "JackUnload"
        },
        {           
            "source_id": "AP8",
            "id": "LM9",
            "task_id": task_id_gen(),
        }
    ]
    
    # Move to start position
    if not goto_start(move_task_list):
        return False
    
    return execute_navigation(move_task_list, "Rack to Dock: AP10 (load) → LM5 → LM9 → AP8 (unload) → LM9")


def courier_dock2rack() -> bool:
    """
    Courier movement from dock to rack: LM4 -> AP3 (load) -> LM4 -> LM5 -> AP7 (unload).
    
    Returns:
        True if task completed successfully
    """
    # Define the move task list
    move_task_list = [
        {
            "source_id": "LM4",
            "id": "AP3",
            "task_id": task_id_gen(),
            "recognize": True,
            "operation": "JackLoad"
        },
        {
            "source_id": "AP3",
            "id": "LM4",
            "task_id": task_id_gen(),
        },
        {
            "source_id": "SELF_POSITION",
            "id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "move_angle": 1.5707963,
            "skill_name": "GoByOdometer",
            "speed_w": 0.5,
            "loc_mode": 1,
        },
        {
            "source_id": "LM4",
            "id": "LM5",
            "task_id": task_id_gen(),
            "spin": True
        },
        {
            "source_id": "LM5",
            "id": "AP7",
            "task_id": task_id_gen(),
            "operation": "JackUnload",
            "spin": True
        }
    ]
    
    # Move to start position
    if not goto_start(move_task_list):
        return False
    
    return execute_navigation(move_task_list, "Courier Dock to Rack: LM4 → AP3 (load) → LM4 → LM5 → AP7 (unload)")


def courier_rack2dock() -> bool:
    """
    Courier movement from rack to dock: Self (load) -> LM5 -> LM4 -> AP3 (unload) -> LM4.
    
    Returns:
        True if task completed successfully
    """
    # Define the move task list
    move_task_list = [
        {
            "source_id": "SELF_POSITION",
            "id": "SELF_POSITION",
            "task_id": task_id_gen(),
            "operation": "JackLoad",
        },
        {
            "source_id": "AP7",
            "id": "LM5",
            "task_id": task_id_gen(),
            "spin": True
        },
        {
            "source_id": "LM5",
            "id": "LM4",
            "task_id": task_id_gen(),
            "spin": True
        },
        {
            "source_id": "LM4",
            "id": "AP3",
            "task_id": task_id_gen(),
            "operation": "JackUnload"
        },
        {
            "source_id": "AP3",
            "id": "LM4",
            "task_id": task_id_gen(),
        }
    ]
    
    # Move to start position
    if not goto_start(move_task_list):
        return False
    
    return execute_navigation(move_task_list, "Courier Rack to Dock: Self (load) → LM5 → LM4 → AP3 (unload) → LM4")    

# ============================================================================
# Interactive Command Interface
# ============================================================================

def print_help():
    """Print available commands."""
    print("\n" + "="*60)
    print("📝 Available Commands")
    print("="*60)
    print("\n🤖 Main Commands:")
    print("  looptest               - Run loop test (LM2 -> LM9 -> LM5 -> LM2)")
    print("  goto <target_id>       - Navigate to a target point by ID")
    print("                           (e.g., goto LM2, goto AP1)")
    
    print("\n🦾 Arm Movement Commands:")
    print("  arm_dock2rack          - Move from dock to rack")
    print("                           (LM9 -> AP8(load) -> LM9 -> LM5 -> AP10(unload))")
    print("  arm_rack2side          - Move from rack to side")
    print("                           (AP10(load) -> LM12 -> AP11(unload))")
    print("  arm_side2rack          - Move from side to rack")
    print("                           (AP11(load) -> LM12 -> AP10(unload))")
    print("  arm_rack2dock          - Move from rack to dock")
    print("                           (AP10(load) -> LM5 -> LM9 -> AP8(unload) -> LM9)")
    
    print("\n� Courier Movement Commands:")
    print("  courier_dock2rack      - Courier from dock to rack")
    print("                           (LM4 -> AP3(load) -> LM4 -> LM5 -> AP7(unload))")
    print("  courier_rack2dock      - Courier from rack to dock")
    print("                           (Self(load) -> LM5 -> LM4 -> AP3(unload) -> LM4)")
    
    print("\n📊 Information:")
    print("  status                 - Display current robot status")
    
    print("\n❓ Other:")
    print("  help                   - Show this help message")
    print("  exit / quit            - Exit program and disconnect")

    
    print("\n💡 Note:")
    print("  Robot connects automatically at startup")
    print("  Robot disconnects automatically at exit")
    print("="*60)


def parse_command(line: str) -> tuple:
    """
    Parse user command line.
    
    Args:
        line: Command line string
        
    Returns:
        Tuple of (command, args)
    """
    parts = line.strip().split()
    if not parts:
        return None, []
    
    command = parts[0].lower()
    args = parts[1:]
    return command, args


def main():
    """Main interactive loop."""
    print("="*60)
    print("🤖 DC Demo 2025 - Interactive Robot Control")
    print("="*60)
    
    # Get robot IP
    robot_ip = input("\nEnter robot IP [192.168.1.123]: ").strip() or "192.168.1.123"
    
    # Auto-connect at start
    print("\n🔌 Connecting to robot...")
    if not connect(robot_ip):
        print("❌ Failed to connect. Exiting.")
        return
    
    print("\nType 'looptest' to run the loop test")
    print("Type 'help' for available commands")
    print("Type 'exit' or 'quit' to exit")
    print("-"*60)
    
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
            command, args = parse_command(line)
            
            if command is None:
                continue
            
            # Handle commands
            try:
                if command in ['exit', 'quit', 'q']:
                    print("\n👋 Exiting...")
                    break
                
                elif command == 'help':
                    print_help()
                
                elif command == 'status':
                    status()
                
                elif command == 'looptest':
                    looptest()
                
                elif command == 'goto':
                    if len(args) < 1:
                        print("❌ Usage: goto <target_id>")
                        print("   Example: goto LM2")
                    else:
                        target_id = args[0]
                        goto(target_id)
                
                elif command == 'arm_dock2rack':
                    arm_dock2rack()
                
                elif command == 'arm_rack2side':
                    arm_rack2side()
                
                elif command == 'arm_side2rack':
                    arm_side2rack()
                
                elif command == 'arm_rack2dock':
                    arm_rack2dock()
                
                elif command == 'courier_dock2rack':
                    courier_dock2rack()
                
                elif command == 'courier_rack2dock':
                    courier_rack2dock()
                
                else:
                    print(f"❌ Unknown command: {command}")
                    print("   Type 'help' for available commands")
            
            except ValueError as e:
                print(f"❌ Invalid parameter: {e}")
            except Exception as e:
                print(f"❌ Error executing command: {e}")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    
    finally:
        # Auto-disconnect at end
        if robot is not None:
            print("\n🔌 Disconnecting from robot...")
            disconnect()
        
        print("\n" + "="*60)
        print("✅ Session ended")
        print("="*60)


if __name__ == "__main__":
    main()

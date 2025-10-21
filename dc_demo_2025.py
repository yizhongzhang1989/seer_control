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
# Test Functions
# ============================================================================

def loop_test() -> bool:
    """
    Execute a loop test navigating through multiple stations: LM2 -> LM9 -> LM5 -> LM2.
    
    Returns:
        True if loop test completed successfully
    """
    if robot is None:
        print("❌ Robot not connected!")
        return False
    
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
    
    print("\n🚀 Loop Test: LM2 → LM9 → LM5 → LM2")
    
    # Send gotargetlist command
    result = robot.task.gotargetlist(move_task_list)
    
    if not result or result.get('ret_code') != 0:
        print("❌ Failed to start task")
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
        print("✅ Loop test completed successfully!\n")
        return True
    else:
        print(f"❌ Loop test failed: {wait_result['status_text']}\n")
        return False


def arm_dock2rack() -> bool:
    """
    Move from dock to rack: LM9 -> AP8 (load) -> LM9 -> LM5 -> AP10 (unload).
    
    Returns:
        True if task completed successfully
    """
    if robot is None:
        print("❌ Robot not connected!")
        return False
    
    # Define the move task list
    move_task_list = [
        {
            "source_id": "LM9",
            "id": "AP8",
            "task_id": task_id_gen(),
            "recognize": False,
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
    
    print("\n🚀 Dock to Rack: LM9 → AP8 (load) → LM9 → LM5 → AP10 (unload)")
    
    # Send gotargetlist command
    result = robot.task.gotargetlist(move_task_list)
    
    if not result or result.get('ret_code') != 0:
        print("❌ Failed to start task")
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
        print("✅ Dock to rack completed successfully!\n")
        return True
    else:
        print(f"❌ Dock to rack failed: {wait_result['status_text']}\n")
        return False    


def arm_rack2side() -> bool:
    """
    Move from rack to side: AP10 (load) -> LM12 -> AP11 (unload).
    
    Returns:
        True if task completed successfully
    """
    if robot is None:
        print("❌ Robot not connected!")
        return False
    
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
    
    print("\n🚀 Rack to Side: AP10 (load) → LM12 → AP11 (unload)")
    
    # Send gotargetlist command
    result = robot.task.gotargetlist(move_task_list)
    
    if not result or result.get('ret_code') != 0:
        print("❌ Failed to start task")
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
        print("✅ Rack to side completed successfully!\n")
        return True
    else:
        print(f"❌ Rack to side failed: {wait_result['status_text']}\n")
        return False    


def arm_side2rack() -> bool:
    """
    Move from side to rack: AP11 (load) -> LM12 -> AP10 (unload).
    
    Returns:
        True if task completed successfully
    """
    if robot is None:
        print("❌ Robot not connected!")
        return False

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
            "recognize": False,
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
    
    print("\n🚀 Side to Rack: AP11 (load) → LM12 → AP10 (unload)")
    
    # Send gotargetlist command
    result = robot.task.gotargetlist(move_task_list)
    
    if not result or result.get('ret_code') != 0:
        print("❌ Failed to start task")
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
        print("✅ Side to rack completed successfully!\n")
        return True
    else:
        print(f"❌ Side to rack failed: {wait_result['status_text']}\n")
        return False    


def arm_rack2dock() -> bool:
    """
    Move from rack to dock: AP10 (load) -> LM5 -> LM9 -> AP8 (unload) -> LM9.
    
    Returns:
        True if task completed successfully
    """
    if robot is None:
        print("❌ Robot not connected!")
        return False
    
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
    
    print("\n🚀 Rack to Dock: AP10 (load) → LM5 → LM9 → AP8 (unload) → LM9")
    
    # Send gotargetlist command
    result = robot.task.gotargetlist(move_task_list)
    
    if not result or result.get('ret_code') != 0:
        print("❌ Failed to start task")
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
        print("✅ Rack to dock completed successfully!\n")
        return True
    else:
        print(f"❌ Rack to dock failed: {wait_result['status_text']}\n")
        return False    

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
    
    print("\n🦾 Arm Movement Commands:")
    print("  dock2rack              - Move from dock to rack")
    print("                           (LM9 -> AP8(load) -> LM9 -> LM5 -> AP10(unload))")
    print("  rack2side              - Move from rack to side")
    print("                           (AP10(load) -> LM12 -> AP11(unload))")
    print("  side2rack              - Move from side to rack")
    print("                           (AP11(load) -> LM12 -> AP10(unload))")
    print("  rack2dock              - Move from rack to dock")
    print("                           (AP10(load) -> LM5 -> LM9 -> AP8(unload) -> LM9)")
    
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
                    loop_test()
                
                elif command == 'dock2rack':
                    arm_dock2rack()
                
                elif command == 'rack2side':
                    arm_rack2side()
                
                elif command == 'side2rack':
                    arm_side2rack()
                
                elif command == 'rack2dock':
                    arm_rack2dock()
                
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

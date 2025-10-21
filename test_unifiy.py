#!/usr/bin/env python3
"""
Test script for unified controller with task_status monitoring

Tests the gotargetlist command with task_status queries using the unified controller.
Path: LM2 -> LM9 -> LM5 -> LM2

Author: Assistant
Date: October 21, 2025
"""

from seer_control import SeerController
import json
import time
from datetime import datetime


# Global counter for task ID generation
_task_id_counter = 0


def task_id_gen() -> str:
    """
    Generate a unique task ID.
    
    Format: YYYYMMDDHHMMSS_N
    Where N is an incrementing counter that resets each time the script runs.
    
    Returns:
        Unique task ID string
        
    Example:
        "20251021143523_1"
        "20251021143523_2"
    """
    global _task_id_counter
    _task_id_counter += 1
    
    # Get current timestamp in format: YYYYMMDDHHMMSS
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Combine timestamp with counter
    task_id = f"{timestamp}_{_task_id_counter}"
    
    return task_id


def test_unified_with_task_status():
    """Test unified controller with gotargetlist and task_status monitoring."""
    
    # Robot connection details
    robot_ip = "192.168.1.123"
    
    # Create unified controller
    print(f"Creating unified controller for robot at {robot_ip}...")
    robot = SeerController(robot_ip)
    
    # Connect to essential services (status, task, control)
    print("\n📡 Connecting to essential services...")
    if not robot.connect_essential():
        print("❌ Failed to connect to essential services")
        return
    
    print("✅ Connected successfully\n")
    
    # Display connection status
    conn_status = robot.get_connection_status()
    print("📊 Connection Status:")
    for service, connected in conn_status.items():
        status_icon = "✅" if connected else "❌"
        print(f"  {status_icon} {service}: {'Connected' if connected else 'Disconnected'}")
    print()
    
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
    
    print("=" * 80)
    print("🚀 Starting Task List: LM2 -> LM9 -> LM5 -> LM2")
    print("=" * 80)
    print("\nMove Task List:")
    print(json.dumps(move_task_list, indent=2))
    print("\n" + "=" * 80)
    
    # Send gotargetlist command using task controller
    print("\n📤 Sending gotargetlist command...")
    result = robot.task.gotargetlist(move_task_list)
    
    # Display result
    print("\n" + "=" * 80)
    print("📥 Response:")
    print("=" * 80)
    if result:
        print(json.dumps(result, indent=2))
        
        # Check return code
        ret_code = result.get('ret_code', -1)
        if ret_code == 0:
            print("\n✅ Task started successfully!")
            print(f"   Task ID: {result.get('task_id', 'N/A')}")
            print(f"   Created: {result.get('create_on', 'N/A')}")
        else:
            print(f"\n⚠️ Task start failed with ret_code: {ret_code}")
            print(f"   Message: {result.get('msg', 'No error message')}")
            # Disconnect and exit if task failed to start
            robot.disconnect_all()
            print("\n✅ Disconnected from robot")
            return
    else:
        print("❌ No response received (connection or timeout error)")
        robot.disconnect_all()
        print("\n✅ Disconnected from robot")
        return
    
    print("=" * 80)
    
    # Monitor task_status in a loop
    print("\n" + "=" * 80)
    print("📊 Monitoring Task Status...")
    print("=" * 80)
    print("(Querying 'task' every 1 second until task_status == 4 (completed))\n")
    
    query_count = 0
    start_time = time.time()
    
    while True:
        query_count += 1
        elapsed = time.time() - start_time
        
        # Query task status (not task_status_package, but task navigation status)
        task_result = robot.status.query_status('task', timeout=2.0)
        
        if task_result:
            # Extract task_status value
            task_status_value = task_result.get('task_status', -1)
            
            # Status meanings (correct definitions):
            # 0 = NONE
            # 1 = WAITING (currently impossible)
            # 2 = RUNNING
            # 3 = SUSPENDED
            # 4 = COMPLETED
            # 5 = FAILED
            # 6 = CANCELED
            status_text = {
                0: "NONE",
                1: "WAITING",
                2: "RUNNING",
                3: "SUSPENDED",
                4: "COMPLETED",
                5: "FAILED",
                6: "CANCELED"
            }.get(task_status_value, "UNKNOWN")
            
            # Extract useful information
            target_id = task_result.get('target_id', 'N/A')
            target_dist = task_result.get('target_dist', 0)
            finished_path = task_result.get('finished_path', [])
            unfinished_path = task_result.get('unfinished_path', [])
            
            # Print compact status
            print(f"[Query #{query_count:3d}] Time: {elapsed:5.1f}s | "
                  f"Status: {task_status_value} ({status_text:10s}) | "
                  f"Target: {target_id:10s} | Dist: {target_dist:6.2f}m | "
                  f"Finished: {len(finished_path)} | Remaining: {len(unfinished_path)}")
            
            # Check task status - only continue if RUNNING (2)
            if task_status_value == 2:
                # Task is running, continue monitoring
                pass
            elif task_status_value == 4:
                # Task completed successfully
                print("\n✅ Task COMPLETED! (task_status == 4)")
                print(f"   Finished path: {' → '.join(finished_path)}")
                break
            elif task_status_value == 5:
                # Task failed
                print("\n❌ Task FAILED! (task_status == 5)")
                print(f"   Finished path: {' → '.join(finished_path)}")
                print(f"   Unfinished path: {' → '.join(unfinished_path)}")
                break
            elif task_status_value == 6:
                # Task canceled
                print("\n⚠️ Task CANCELED! (task_status == 6)")
                print(f"   Finished path: {' → '.join(finished_path)}")
                print(f"   Unfinished path: {' → '.join(unfinished_path)}")
                break
            elif task_status_value == 3:
                # Task suspended
                print("\n⏸️ Task SUSPENDED! (task_status == 3)")
                print(f"   Finished path: {' → '.join(finished_path)}")
                print(f"   Unfinished path: {' → '.join(unfinished_path)}")
                break
            elif task_status_value == 0:
                # Task is NONE
                print("\n⚠️ Task status is NONE! (task_status == 0)")
                break
            else:
                # Unknown status
                print(f"\n⚠️ Unknown task status: {task_status_value}")
                break
        else:
            print(f"[Query #{query_count:3d}] Time: {elapsed:5.1f}s | ❌ Failed to query task status")
        
        # Wait 1 second before next query
        time.sleep(1)
    
    # Final status summary
    print("\n" + "=" * 80)
    print("📊 Final Statistics")
    print("=" * 80)
    
    # Get statistics from all controllers
    all_stats = robot.get_all_stats()
    print("\nController Statistics:")
    for controller_name, stats in all_stats.items():
        # Check if controller has any activity
        commands_sent = stats.get('commands_sent', 0)
        responses_received = stats.get('responses_received', 0)
        if commands_sent > 0 or responses_received > 0:
            print(f"\n  {controller_name}:")
            for key, value in stats.items():
                print(f"    {key}: {value}")
    
    # Print status summary
    print("\n" + "=" * 80)
    print("🤖 Robot Status Summary")
    print("=" * 80)
    robot.print_status_summary()
    
    # Disconnect from all services
    robot.disconnect_all()
    print("\n✅ Disconnected from all services")


if __name__ == "__main__":
    test_unified_with_task_status()

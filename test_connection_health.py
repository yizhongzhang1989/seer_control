#!/usr/bin/env python3
"""
Test script to monitor connection health detection.

This script connects to the robot and continuously monitors the connection
health status. You can disconnect the network while this is running to see
how quickly the disconnection is detected.

Usage:
    python test_connection_health.py
"""

import time
from smart_seer_controller import SmartSeerController

def main():
    ROBOT_IP = "192.168.12.163"
    
    print("="*60)
    print("Connection Health Monitoring Test")
    print("="*60)
    
    # Create controller
    ctrl = SmartSeerController(ROBOT_IP)
    
    # Connect to robot
    print("\n1. Connecting to robot...")
    if not ctrl.connect():
        print("❌ Failed to connect!")
        return
    
    print("\n2. Starting connection health monitoring...")
    print("   (Disconnect the network to test detection)\n")
    
    check_count = 0
    last_status = True
    
    try:
        while True:
            check_count += 1
            print(f"\n--- Health Check #{check_count} ---")
            
            # Check connection health with verbose output
            is_healthy = ctrl.check_connection_health(verbose=True)
            
            # Detect status change
            if is_healthy != last_status:
                if is_healthy:
                    print("\n🟢 CONNECTION RESTORED")
                else:
                    print("\n🔴 CONNECTION LOST DETECTED!")
                last_status = is_healthy
            
            # Wait before next check
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\n3. Shutting down...")
        ctrl.disconnect()
        print("✅ Disconnected successfully")

if __name__ == "__main__":
    main()

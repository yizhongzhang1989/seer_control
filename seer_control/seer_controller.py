#!/usr/bin/env python3
"""
SEER Unified Robot Controller

A unified connection manager that provides access to all SEER robot controllers:
- Status queries (65+ commands on port 19204)
- Task/Motion control (16 commands on port 19206)
- Control operations (9 commands on port 19205)
- Configuration (38 commands on port 19207)
- Other operations (55 commands on port 19210)
- Push data monitoring (port 19301)

This controller manages connections to all services and provides direct access
to specialized controllers through public properties.

Usage:
    # Create controller and connect
    controller = SeerController(robot_ip='192.168.1.123')
    controller.connect_all()  # or connect_essential()
    
    # Access specialized controllers directly
    position = controller.status.query_status('loc')
    controller.task.gotarget(id="Station1")
    controller.control.start()
    controller.config.set_max_speed(v=1.5)
    controller.other.jack_load()
    
    # Disconnect when done
    controller.disconnect_all()

Author: Assistant
Date: October 21, 2025
"""

from typing import Dict, Any
from .seer_status_controller import SeerStatusController
from .seer_task_controller import SeerTaskController
from .seer_control_controller import SeerControlController
from .seer_config_controller import SeerConfigController
from .seer_other_controller import SeerOtherController
from .seer_push_controller import SeerPushController


class SeerController:
    """
    Unified SEER Robot Controller - Connection Manager.
    
    Manages connections to all specialized controllers and provides direct access.
    Each specialized controller operates on its designated port:
    - status: 19204 - SeerStatusController (query_status, get_stats, etc.)
    - task: 19206 - SeerTaskController (gotarget, translate, turn, etc.)
    - control: 19205 - SeerControlController (start, stop, reloc, etc.)
    - config: 19207 - SeerConfigController (set_max_speed, configure_push, etc.)
    - other: 19210 - SeerOtherController (jack_load, jack_unload, etc.)
    - push: 19301 - SeerPushController (configure_push, start_listening, etc.)
    
    Example:
        controller = SeerController('192.168.1.123')
        controller.connect_essential()
        
        # Access controllers directly
        pos = controller.status.query_status('loc')
        controller.task.gotarget(id="Station1")
        controller.control.pause()
        
        controller.disconnect_all()
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5'):
        """
        Initialize the unified controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
        """
        self.robot_ip = robot_ip
        
        # Initialize all specialized controllers
        self.status = SeerStatusController(robot_ip, 19204)
        self.task = SeerTaskController(robot_ip, 19206)
        self.control = SeerControlController(robot_ip, 19205)
        self.config = SeerConfigController(robot_ip, 19207)
        self.other = SeerOtherController(robot_ip, 19210)
        self.push = SeerPushController(robot_ip, 19301)
        
        # Track connection status
        self._connections = {
            'status': False,
            'task': False,
            'control': False,
            'config': False,
            'other': False,
            'push': False
        }
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    def connect_all(self, timeout: float = 5.0) -> Dict[str, bool]:
        """
        Connect to all robot services.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            Dictionary showing connection status for each service
        """
        self._connections['status'] = self.status.connect(timeout)
        self._connections['task'] = self.task.connect(timeout)
        self._connections['control'] = self.control.connect(timeout)
        self._connections['config'] = self.config.connect(timeout)
        self._connections['other'] = self.other.connect(timeout)
        # Note: Push controller connects separately when needed
        
        return self._connections.copy()
    
    def connect_essential(self, timeout: float = 5.0) -> Dict[str, bool]:
        """
        Connect to essential services only (status, task, control).
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            Dictionary showing connection status for essential services
        """
        self._connections['status'] = self.status.connect(timeout)
        self._connections['task'] = self.task.connect(timeout)
        self._connections['control'] = self.control.connect(timeout)
        
        return {
            'status': self._connections['status'],
            'task': self._connections['task'],
            'control': self._connections['control']
        }
    
    def disconnect_all(self):
        """Disconnect from all robot services."""
        self.status.disconnect()
        self.task.disconnect()
        self.control.disconnect()
        self.config.disconnect()
        self.other.disconnect()
        self.push.stop_listening()
        
        for key in self._connections:
            self._connections[key] = False
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Get current connection status for all services."""
        return self._connections.copy()
    
    # ========================================================================
    # Statistics and Information
    # ========================================================================
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics from all controllers.
        
        Returns:
            Dictionary with stats from each controller
        """
        return {
            'status': self.status.get_stats(),
            'task': self.task.get_stats(),
            'control': self.control.get_stats(),
            'config': self.config.get_stats(),
            'other': self.other.get_stats(),
            'push': self.push.get_stats()
        }
    
    def print_status_summary(self):
        """Print a summary of robot status."""
        print("="*60)
        print("SEER Robot Status Summary")
        print("="*60)
        
        # Connection status
        print("\n📡 Connections:")
        for service, connected in self._connections.items():
            status = "✅ Connected" if connected else "❌ Disconnected"
            print(f"  {service:12s}: {status}")
        
        # Get location if connected
        if self._connections['status']:
            loc = self.status.query_status('loc')
            if loc and loc.get('ret_code') == 0:
                print("\n📍 Position:")
                print(f"  X: {loc.get('x', 'N/A'):.3f} m")
                print(f"  Y: {loc.get('y', 'N/A'):.3f} m")
                print(f"  Angle: {loc.get('angle', 'N/A'):.3f} rad")
        
        # Get battery if connected
        if self._connections['status']:
            battery = self.status.query_status('battery')
            if battery and battery.get('ret_code') == 0:
                print("\n🔋 Battery:")
                print(f"  Level: {battery.get('battery', 'N/A')}%")
        
        print("="*60)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"SeerController(robot_ip='{self.robot_ip}')"
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        connected_count = sum(1 for v in self._connections.values() if v)
        return f"SeerController({self.robot_ip}, {connected_count}/6 services connected)"


def main():
    """
    Interactive command-line interface for the unified controller.
    """
    from .util import parse_command_line
    
    print("🤖 SEER Unified Controller - Interactive Mode")
    print("=" * 60)
    
    # Create unified controller
    robot_ip = input("Enter robot IP [192.168.1.123]: ").strip() or "192.168.1.123"
    controller = SeerController(robot_ip=robot_ip)
    print(f"\n✅ Controller created: {controller}")
    
    # Connect to essential services
    print("\n🔌 Connecting to essential services...")
    connections = controller.connect_essential()
    
    for service, connected in connections.items():
        status = "✅" if connected else "❌"
        print(f"  {status} {service}")
    
    if not any(connections.values()):
        print("\n❌ Failed to connect to any services. Exiting.")
        return
    
    # Show status summary
    print("\n")
    controller.print_status_summary()
    
    # Interactive command loop
    print("\n" + "=" * 60)
    print("📝 Interactive Command Mode")
    print("=" * 60)
    print("\nAvailable command categories:")
    print("  Status:  query_robot_status_loc, query_battery, query_version")
    print("  Motion:  gotarget, translate, turn, pause, resume, cancel")
    print("  Control: start, stop, reloc, estop, standby")
    print("  Config:  set_max_speed, set_obstacle_distance")
    print("  Other:   jack_load, jack_unload, jack_set_height")
    print("\nType 'help' for more info, 'status' for robot status, 'exit' to quit")
    print("-" * 60)
    
    try:
        while True:
            try:
                line = input("\n🤖 > ").strip()
            except EOFError:
                print("\n")
                break
            
            if not line:
                continue
            
            if line.lower() in ['exit', 'quit', 'q']:
                print("👋 Exiting...")
                break
            
            if line.lower() == 'help':
                print("\nCommands:")
                print("  status                    - Show robot status")
                print("  query_robot_status_loc    - Query position")
                print("  gotarget id=Station1      - Navigate to station")
                print("  translate dist=1.0 vx=0.5 - Move forward")
                print("  turn angle=1.57 vw=0.5    - Rotate")
                print("  pause                     - Pause motion")
                print("  resume                    - Resume motion")
                print("  start                     - Start robot")
                print("  stop                      - Stop robot")
                continue
            
            if line.lower() == 'status':
                controller.print_status_summary()
                continue
            
            # Parse and execute command
            func_name, params = parse_command_line(line)
            
            if not func_name:
                print("❌ Invalid command format")
                continue
            
            if not hasattr(controller, func_name):
                print(f"❌ Unknown command: {func_name}")
                print("   Type 'help' for available commands")
                continue
            
            func = getattr(controller, func_name)
            
            try:
                print(f"⚙️  Calling {func_name}({', '.join(f'{k}={v}' for k, v in params.items())})")
                result = func(**params)
                
                if result is not None:
                    ret_code = result.get('ret_code', -1)
                    if ret_code == 0:
                        print("✅ Command succeeded!")
                        if len(result) > 1:
                            print(f"   Response: {result}")
                    else:
                        error_msg = result.get('err_msg', 'Unknown error')
                        print(f"❌ Command failed with code {ret_code}: {error_msg}")
                else:
                    print("❌ Command failed - no response received")
                    
            except TypeError as e:
                print(f"❌ Invalid parameters: {e}")
            except Exception as e:
                print(f"❌ Error executing command: {e}")
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    
    finally:
        # Disconnect
        controller.disconnect_all()
        print("\n🔌 Disconnected from all services")
        print("\n" + "=" * 60)
        print("✅ Session ended!")
        print("=" * 60)


if __name__ == "__main__":
    main()

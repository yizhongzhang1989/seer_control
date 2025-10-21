#!/usr/bin/env python3
"""
SEER Robot Control Controller

This module provides control functions for SEER robots.
Each control command has its own dedicated function with specific parameters.

Features:
- Motion control (stop, open-loop motion)
- Localization control (confirm, relocate, cancel relocate)
- Map management (load map, upload and load map)
- Calibration (motor encoder zero, weight sensor zero)

Control commands:
- Motion: stop, motion (open-loop)
- Localization: comfirmloc, reloc, cancelreloc
- Map: loadmap, upload_and_loadmap
- Calibration: clearmotorencoder, clear_weightdevvalue

Manual: https://seer-group.feishu.cn/wiki/WsI2wM46YiESh8k12EBclv23nOf?table=tblObW6PmjUPTyTn&view=vewiqqgyEX

Author: Assistant
Date: October 18, 2025
"""

from typing import Optional, Dict, Any, List
from .seer_controller_base import SeerControllerBase


# Control command IDs
# Format: (request_id, response_id, description)
CONTROL_COMMANDS = {
    'stop': (2000, 12000, 'Stop open-loop motion'),
    'comfirmloc': (2003, 12003, 'Confirm localization correct'),
    'reloc': (2002, 12002, 'Relocate robot'),
    'cancelreloc': (2004, 12004, 'Cancel relocate'),
    'motion': (2010, 12010, 'Open-loop motion'),
    'loadmap': (2022, 12022, 'Switch loaded map'),
    'clearmotorencoder': (2024, 12024, 'Clear motor encoder to zero'),
    'clear_weightdevvalue': (2026, 12026, 'Clear weight sensor to zero'),
    'upload_and_loadmap': (2025, 12025, 'Upload and switch loaded map'),
}


class SeerControlController(SeerControllerBase):
    """
    SEER Robot Control Controller.
    
    Provides dedicated functions for each control command.
    Each command has specific parameters and JSON payload structure.
    
    Example:
        controller = SeerControlController('192.168.192.5', 19205)
        controller.connect()
        
        # Stop robot
        result = controller.stop()
        
        # Relocate robot
        result = controller.reloc(x=0.0, y=0.0, angle=0.0)
        
        # Load map
        result = controller.loadmap(map_name="factory_floor1")
        
        controller.disconnect()
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19205):
        """
        Initialize the control controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
            robot_port: Port number for control commands (default: 19205)
        """
        super().__init__(robot_ip, robot_port)
    
    def stop(self) -> Optional[Dict[str, Any]]:
        """
        Stop open-loop motion - Halt all open-loop movements.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.stop()
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['stop']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def comfirmloc(self, **params) -> Optional[Dict[str, Any]]:
        """
        Confirm localization correct - Confirm robot's current localization.
        
        Args:
            **params: Confirmation parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.comfirmloc()
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['comfirmloc']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def reloc(self, **params) -> Optional[Dict[str, Any]]:
        """
        Relocate robot - Force robot to relocate to specified position.
        
        Args:
            **params: Relocation parameters (to be specified)
                - x: X coordinate
                - y: Y coordinate
                - angle: Orientation angle
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.reloc(x=0.0, y=0.0, angle=0.0)
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['reloc']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def cancelreloc(self, **params) -> Optional[Dict[str, Any]]:
        """
        Cancel relocate - Cancel ongoing relocation process.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.cancelreloc()
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['cancelreloc']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def motion(
        self, 
        vx: float = 0.0,
        vy: float = 0.0,
        w: float = 0.0,
        steer: Optional[int] = None,
        real_steer: Optional[float] = None,
        duration: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Open-loop motion - Control robot with open-loop motion commands.
        
        Args:
            vx: Linear velocity in robot X-axis direction (m/s), default 0
            vy: Linear velocity in robot Y-axis direction (m/s), default 0
            w: Angular velocity (rad/s, clockwise=negative, counterclockwise=positive), default 0
            steer: Steer angle control for single-steer robots:
                   -2 = reset to zero
                   1 = increase by 15°
                   -1 = decrease by 15°
                   When present, vy and w are ignored, vx becomes steer wheel linear speed
            real_steer: Target steer angle (rad) for single-steer robots (robot coordinate system)
                        When present, vy and w are ignored, vx becomes steer wheel linear speed
                        Has higher priority than steer
            duration: Duration of open-loop motion (ms)
                      0 = continuous motion at current speed
                      If omitted, uses ControlMotionDuration from config
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            # Normal differential drive motion
            result = controller.motion(vx=0.5, vy=0.0, w=0.0, duration=2000)
            
            # Single-steer robot with specific angle
            result = controller.motion(vx=1.0, real_steer=0.52, duration=3000)
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['motion']
        
        params = {
            'vx': vx,
            'vy': vy,
            'w': w
        }
        
        # Add optional parameters if provided
        if steer is not None:
            params['steer'] = steer
        if real_steer is not None:
            params['real_steer'] = real_steer
        if duration is not None:
            params['duration'] = duration
        
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def loadmap(self, **params) -> Optional[Dict[str, Any]]:
        """
        Switch loaded map - Load a different map.
        
        Args:
            **params: Map loading parameters (to be specified)
                - map_name: Name of the map to load
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.loadmap(map_name="factory_floor1")
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['loadmap']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def clearmotorencoder(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear motor encoder to zero - Reset motor encoder values.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clearmotorencoder()
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['clearmotorencoder']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clear_weightdevvalue(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear weight sensor to zero - Reset weight sensor calibration.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clear_weightdevvalue()
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['clear_weightdevvalue']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def upload_and_loadmap(self, **params) -> Optional[Dict[str, Any]]:
        """
        Upload and switch loaded map - Upload new map and switch to it.
        
        Args:
            **params: Upload and load parameters (to be specified)
                - map_name: Name of the map
                - map_data: Map file data
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.upload_and_loadmap(map_name="new_map", map_data=...)
        """
        req_id, resp_id, desc = CONTROL_COMMANDS['upload_and_loadmap']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=30.0  # Longer timeout for upload
        )
    
    @staticmethod
    def get_available_commands() -> List[str]:
        """
        Get list of all available control commands.
        
        Returns:
            List of command name strings
        """
        return list(CONTROL_COMMANDS.keys())
    
    @staticmethod
    def get_command_info(command: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific command.
        
        Args:
            command: Command name string (e.g., 'stop', 'reloc')
            
        Returns:
            Dictionary with command information:
            - request_id: Request message ID
            - response_id: Response message ID
            - description: Human-readable description
            Returns None if command not found
        """
        if command not in CONTROL_COMMANDS:
            return None
        
        req_id, resp_id, desc = CONTROL_COMMANDS[command]
        return {
            'request_id': req_id,
            'response_id': resp_id,
            'description': desc
        }


def main():
    """
    Interactive command-line interface for testing control commands.
    
    Allows entering commands like:
        stop
        reloc x=0.0 y=0.0 angle=0.0
        loadmap map_name=factory_floor1
        exit
    """
    from util import parse_command_line
    
    print("🤖 SEER Control Controller - Interactive Mode")
    print("=" * 60)
    
    # Create controller
    controller = SeerControlController(robot_ip='192.168.1.123', robot_port=19205)
    print(f"Controller: {controller}")
    
    # Show available commands
    commands = controller.get_available_commands()
    print(f"\nAvailable commands ({len(commands)} total):")
    for cmd in commands:
        info = controller.get_command_info(cmd)
        print(f"  - {cmd:25s} : {info['description']}")
    
    # Connect to robot
    print("\n🔌 Connecting to robot...")
    if not controller.connect():
        print("❌ Failed to connect to robot")
        return
    
    print("✅ Connected successfully!")
    
    # Interactive command loop
    print("\n" + "=" * 60)
    print("📝 Interactive Command Mode")
    print("=" * 60)
    print("\nEnter commands in the format:")
    print("  <function_name> <param1>=<value1> <param2>=<value2> ...")
    print("\nExamples:")
    print("  stop")
    print("  comfirmloc")
    print("  reloc x=0.0 y=0.0 angle=0.0")
    print("  loadmap map_name=factory_floor1")
    print("  motion vx=0.5 vy=0.0 w=0.0 duration=2000")
    print("  motion vx=1.0 real_steer=0.52 duration=3000")
    print("\nType 'exit' or 'quit' to disconnect and exit.")
    print("Type 'help' to show available commands.")
    print("-" * 60)
    
    try:
        while True:
            # Get user input
            try:
                line = input("\n🎮 > ").strip()
            except EOFError:
                print("\n")
                break
            
            if not line:
                continue
            
            # Check for exit commands
            if line.lower() in ['exit', 'quit', 'q']:
                print("� Exiting...")
                break
            
            # Check for help command
            if line.lower() == 'help':
                print("\nAvailable commands:")
                for cmd in commands:
                    info = controller.get_command_info(cmd)
                    print(f"  - {cmd:25s} : {info['description']}")
                continue
            
            # Parse command line
            func_name, params = parse_command_line(line)
            
            if not func_name:
                print("❌ Invalid command format")
                continue
            
            # Check if function exists
            if not hasattr(controller, func_name):
                print(f"❌ Unknown command: {func_name}")
                print(f"   Type 'help' to see available commands")
                continue
            
            # Get the function
            func = getattr(controller, func_name)
            
            # Call the function with error handling
            try:
                print(f"📤 Calling {func_name}({', '.join(f'{k}={v}' for k, v in params.items())})")
                result = func(**params)
                
                if result is not None:
                    # Check return code
                    ret_code = result.get('ret_code', -1)
                    if ret_code == 0:
                        print(f"✅ Command succeeded!")
                        # Show result data
                        if len(result) > 1:  # More than just ret_code
                            print(f"   Response: {result}")
                    else:
                        error_msg = result.get('err_msg', 'Unknown error')
                        print(f"❌ Command failed with code {ret_code}: {error_msg}")
                        if len(result) > 2:  # More details
                            print(f"   Full response: {result}")
                else:
                    print(f"❌ Command failed - no response received")
                    
            except TypeError as e:
                print(f"❌ Invalid parameters: {e}")
                print(f"   Usage: Check function signature or documentation")
            except Exception as e:
                print(f"❌ Error executing command: {e}")
                import traceback
                traceback.print_exc()
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    
    finally:
        # Disconnect
        controller.disconnect()
        print("\n🔌 Disconnected")
        print("\n" + "=" * 60)
        print("✅ Session ended!")
        print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SEER Robot Task Controller

This module provides task and motion control functions for SEER robots.
Each control command has its own dedicated function with specific parameters.

Features:
- Path navigation (single target, multi-target, circular)
- Motion control (translate, rotate, spin)
- Path management (enable/disable, clear)
- Task control (pause, resume, cancel)
- Task chain management

Control commands:
- Task: gotarget, gotargetlist, translate, turn, circular, spin
- Control: pause, resume, cancel
- Path: path (enable/disable), cleartargetlist, safeclearmovements
- Task Chain: tasklist_status, tasklist_list, tasklist_name, target_path

Manual: https://seer-group.feishu.cn/wiki/WsI2wM46YiESh8k12EBclv23nOf?table=tblObW6PmjUPTyTn&view=vewiqqgyEX

Author: Assistant
Date: October 18, 2025
"""

import time
from typing import Optional, Dict, Any, List
try:
    from .seer_controller_base import SeerControllerBase
except ImportError:
    from seer_controller_base import SeerControllerBase


# Task control command IDs
# Format: (request_id, response_id, description)
TASK_COMMANDS = {
    'gotarget': (3051, 13051, 'Path navigation'),
    'gotargetlist': (3066, 13066, 'Specified path navigation'),
    'translate': (3055, 13055, 'Translation'),
    'turn': (3056, 13056, 'Rotation'),
    'circular': (3058, 13058, 'Circular motion'),
    'path': (3059, 13059, 'Enable and disable routes'),
    'spin': (3057, 13057, 'Pallet rotation'),
    'pause': (3001, 13001, 'Pause current task'),
    'resume': (3002, 13002, 'Resume current task'),
    'cancel': (3003, 13003, 'Cancel current task'),
    'tasklist_status': (3101, 13101, 'Query robot task chain'),
    'tasklist_list': (3115, 13115, 'Query all robot task chains'),
    'tasklist_name': (3106, 13106, 'Execute pre-stored task chain'),
    'target_path': (3053, 13053, 'Get path navigation path'),
    'cleartargetlist': (3067, 13067, 'Clear specified navigation path'),
    'safeclearmovements': (3068, 13068, 'Clear specified navigation path by task id'),
}


class SeerTaskController(SeerControllerBase):
    """
    SEER Robot Task Controller.
    
    Provides dedicated functions for each task and motion control command.
    Each command has specific parameters and JSON payload structure.
    
    Example:
        controller = SeerTaskController('192.168.192.5', 19206)
        controller.connect()
        
        # Navigate to target
        result = controller.gotarget(x=1.0, y=2.0, angle=0.0)
        
        # Rotate robot
        result = controller.turn(angle=1.57, angular_velocity=0.5)
        
        # Pause task
        result = controller.pause()
        
        controller.disconnect()
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19206):
        """
        Initialize the task controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
            robot_port: Port number for motion control (default: 19206)
        """
        super().__init__(robot_ip, robot_port)
    
    def gotarget(self, 
                 id: Optional[str] = None,
                 source_id: Optional[str] = None,
                 task_id: Optional[str] = None,
                 spin: Optional[bool] = None,
                 operation: Optional[str] = None,
                 **params) -> Optional[Dict[str, Any]]:
        """
        Path navigation - Navigate robot to target position.
        
        Manual: https://seer-group.feishu.cn/wiki/Q26SwaNoGisuLWk2vCxcPfVWn2e
        
        This function supports many parameters. Frequently used parameters are explicitly
        defined, and additional parameters can be passed via **params.
        
        Args:
            id: Target station name. Use "SELF_POSITION" when executing operation in place
                - Optional parameter
            source_id: Starting station name. Use "SELF_POSITION" when starting from 
                       current robot position (not at a station)
                - Optional parameter
            task_id: Task number/identifier
                - Optional parameter
            spin: Whether to enable follow-up rotation
                - Optional parameter
            operation: Control jack device action, supported actions:
                - "JackLoad": Jack up to load cargo (sets robot to loaded state)
                - "JackUnload": Jack down to unload cargo (sets robot to unloaded state)
                - "JackHeight": Jack to height
                - "Wait": No action (default)
                - Optional parameter, defaults to "Wait"
            **params: Additional navigation parameters as key-value pairs.
                      These will be merged with explicitly defined parameters.
                      Can include: jack_height, x, y, z, etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Examples:
            # Navigate to a named station
            result = controller.gotarget(id="Station1")
            
            # Navigate from current position to target
            result = controller.gotarget(id="Station2", source_id="SELF_POSITION", spin=True)
            
            # Execute action at current position
            result = controller.gotarget(id="SELF_POSITION")
            
            # Navigate with task ID
            result = controller.gotarget(id="Station3", task_id="TASK_001")
            
            # Jack up to load cargo at station
            result = controller.gotarget(id="LoadStation", operation="JackLoad", jack_height=0.5)
            
            # Jack down to unload cargo
            result = controller.gotarget(id="UnloadStation", operation="JackUnload", jack_height=0.0)
            
            # Jack to specific height
            result = controller.gotarget(id="Station4", operation="JackHeight", jack_height=0.3)
            
            # Using additional parameters (including angle via **params)
            result = controller.gotarget(id="Station5", x=1.0, y=2.0, z=0.0, angle=1.57)
        """
        req_id, resp_id, desc = TASK_COMMANDS['gotarget']
        
        # Build payload starting with params
        payload = dict(params)
        
        # Add explicitly defined parameters if provided (they override params)
        if id is not None:
            payload['id'] = id
        if source_id is not None:
            payload['source_id'] = source_id
        if task_id is not None:
            payload['task_id'] = task_id
        if spin is not None:
            payload['spin'] = spin
        if operation is not None:
            payload['operation'] = operation
        
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=payload,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def gotargetlist(self, move_task_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Specified path navigation - Navigate through multiple targets.
        
        Args:
            move_task_list: List of movement tasks, where each task is a dictionary containing:
                - id: Target station name (required)
                - source_id: Starting station name (required)
                - task_id: Task identifier (required)
                - operation: Optional operation (e.g., "JackLoad", "JackUnload", "JackHeight")
                - jack_height: Optional jack height in meters (used with "JackHeight" operation)
                - Other optional parameters
        
        Returns:
            Response dictionary if successful, None if failed
            
        Examples:
            # Simple path navigation
            tasks = [
                {"id": "LM2", "source_id": "LM1", "task_id": "00000001"},
                {"id": "LM3", "source_id": "LM2", "task_id": "00000002"}
            ]
            result = controller.gotargetlist(tasks)
            
            # Path with jack operations
            tasks = [
                {"id": "LM2", "source_id": "LM1", "task_id": "00000001"},
                {
                    "id": "AP1", 
                    "source_id": "LM2", 
                    "task_id": "00000002",
                    "operation": "JackHeight",
                    "jack_height": 0.2
                }
            ]
            result = controller.gotargetlist(tasks)
        """
        req_id, resp_id, desc = TASK_COMMANDS['gotargetlist']
        
        # Convert list to dict format expected by the robot
        payload = {
            'move_task_list': move_task_list
        }
        
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=payload,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def translate(self, dist: float, vx: Optional[float] = None, 
                  vy: Optional[float] = None, mode: int = 0) -> Optional[Dict[str, Any]]:
        """
        Translation - Move robot in straight line.
        
        Manual: https://seer-group.feishu.cn/wiki/NhfPwV2L2ij5iXkrsmBcZQR1n0e
        
        Args:
            dist: Linear motion distance (absolute value) in meters
            vx: Velocity in X direction in robot coordinate system (m/s)
                - Positive: forward, Negative: backward
                - Optional, can be omitted
            vy: Velocity in Y direction in robot coordinate system (m/s)
                - Positive: left, Negative: right
                - Optional, can be omitted
            mode: 0=odometry mode (motion based on odometry), 1=localization mode
                  Default: 0 (odometry mode)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            # Move forward 1 meter
            result = controller.translate(dist=1.0, vx=0.5)
            
            # Move backward 0.5 meters
            result = controller.translate(dist=0.5, vx=-0.3)
            
            # Move left (with both vx and vy)
            result = controller.translate(dist=1.0, vx=0.3, vy=0.3)
        """
        req_id, resp_id, desc = TASK_COMMANDS['translate']
        
        # Build payload with required parameter
        payload = {
            'dist': abs(dist),  # Absolute value
            'mode': mode
        }
        
        # Add optional parameters if provided
        if vx is not None:
            payload['vx'] = vx
        if vy is not None:
            payload['vy'] = vy
        
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=payload,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def turn(self, angle: float, vw: float, mode: int = 0) -> Optional[Dict[str, Any]]:
        """
        Rotation - Rotate robot by specified angle.
        
        Manual: https://seer-group.feishu.cn/wiki/GuERwubRriOJzskwWGecYCtpn5f
        
        Args:
            angle: Rotation angle in radians (absolute value)
            vw: Angular velocity in rad/s (positive=CCW, negative=CW)
            mode: 0=odometry mode, 1=localization mode (default: 0)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            # Rotate 90 degrees counterclockwise at 0.5 rad/s
            result = controller.turn(angle=1.57, vw=0.5, mode=0)
        """
        req_id, resp_id, desc = TASK_COMMANDS['turn']
        
        payload = {
            'angle': abs(angle),  # Protocol requires absolute value
            'vw': vw,
            'mode': mode
        }
        
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=payload,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def circular(self, rot_radius: Optional[float] = None, 
                 rot_degree: Optional[float] = None,
                 rot_speed: Optional[float] = None, 
                 mode: int = 0) -> Optional[Dict[str, Any]]:
        """
        Circular motion - Move robot in circular arc.
        
        Manual: https://seer-group.feishu.cn/wiki/GuERwubRriOJzskwWGecYCtpn5f
        
        Args:
            rot_radius: Rotation radius in meters
                - Positive: center on robot's left side
                - Negative: center on robot's right side
                - Optional parameter
            rot_degree: Rotation angle in degrees
                - Optional parameter
            rot_speed: Rotation speed in rad/s
                - Positive: counterclockwise
                - Negative: clockwise
                - Optional parameter
            mode: 0=odometry mode (motion based on odometry), 1=localization mode
                  Default: 0 (odometry mode)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            # Arc with 1m radius, 90 degrees, 0.5 rad/s
            result = controller.circular(rot_radius=1.0, rot_degree=90, rot_speed=0.5)
            
            # Clockwise arc (negative speed)
            result = controller.circular(rot_radius=0.5, rot_degree=180, rot_speed=-0.5)
            
            # Center on right side (negative radius)
            result = controller.circular(rot_radius=-1.0, rot_degree=45, rot_speed=0.3)
        """
        req_id, resp_id, desc = TASK_COMMANDS['circular']
        
        # Build payload with mode
        payload = {
            'mode': mode
        }
        
        # Add optional parameters if provided
        if rot_radius is not None:
            payload['rot_radius'] = rot_radius
        if rot_degree is not None:
            payload['rot_degree'] = rot_degree
        if rot_speed is not None:
            payload['rot_speed'] = rot_speed
        
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=payload,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def path(self, **params) -> Optional[Dict[str, Any]]:
        """
        Enable and disable routes - Control path availability.
        
        Args:
            **params: Path control parameters (to be specified)
                - Path identifiers
                - Enable/disable flag
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.path(path_id="route1", enable=True)
        """
        req_id, resp_id, desc = TASK_COMMANDS['path']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def spin(self, increase_spin_angle: Optional[float] = None,
             robot_spin_angle: Optional[float] = None,
             global_spin_angle: Optional[float] = None,
             spin_direction: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Pallet rotation - Rotate pallet or payload.
        
        Manual: https://seer-group.feishu.cn/wiki/HIanw4DZsirojfkIvPdcx4k3nTh
        
        Args:
            increase_spin_angle: Increase angle from current pallet angle
                - Positive: counterclockwise rotation
                - Negative: clockwise rotation
                - Optional parameter
            robot_spin_angle: Rotate pallet to an angle in robot coordinate system
                - spin_direction=0: nearest direction
                - spin_direction=1: counterclockwise
                - spin_direction=-1: clockwise
                - Optional parameter
            global_spin_angle: Rotate pallet to an angle in world coordinate system
                - spin_direction=0: nearest direction
                - spin_direction=1: counterclockwise
                - spin_direction=-1: clockwise
                - Optional parameter
            spin_direction: Direction control
                - 0: nearest direction
                - 1: counterclockwise
                - -1: clockwise
                - Optional parameter (used with robot_spin_angle or global_spin_angle)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            # Increase current angle by 45 degrees counterclockwise
            result = controller.spin(increase_spin_angle=45)
            
            # Rotate to 90 degrees in robot coordinate (nearest direction)
            result = controller.spin(robot_spin_angle=90, spin_direction=0)
            
            # Rotate to 180 degrees in world coordinate (counterclockwise)
            result = controller.spin(global_spin_angle=180, spin_direction=1)
            
            # Decrease angle by 30 degrees (clockwise)
            result = controller.spin(increase_spin_angle=-30)
        """
        req_id, resp_id, desc = TASK_COMMANDS['spin']
        
        # Build payload with optional parameters
        payload = {}
        
        if increase_spin_angle is not None:
            payload['increase_spin_angle'] = increase_spin_angle
        if robot_spin_angle is not None:
            payload['robot_spin_angle'] = robot_spin_angle
        if global_spin_angle is not None:
            payload['global_spin_angle'] = global_spin_angle
        if spin_direction is not None:
            payload['spin_direction'] = spin_direction
        
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=payload,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def pause(self) -> Optional[Dict[str, Any]]:
        """
        Pause current navigation - Temporarily halt robot movement.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.pause()
        """
        req_id, resp_id, desc = TASK_COMMANDS['pause']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def resume(self) -> Optional[Dict[str, Any]]:
        """
        Resume current navigation - Continue paused movement.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.resume()
        """
        req_id, resp_id, desc = TASK_COMMANDS['resume']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def cancel(self) -> Optional[Dict[str, Any]]:
        """
        Cancel current navigation - Stop and clear current task.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.cancel()
        """
        req_id, resp_id, desc = TASK_COMMANDS['cancel']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def tasklist_status(self, **params) -> Optional[Dict[str, Any]]:
        """
        Query robot task chain - Get current task chain status.
        
        Args:
            **params: Query parameters (to be specified)
                - Task chain identifier
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.tasklist_status()
        """
        req_id, resp_id, desc = TASK_COMMANDS['tasklist_status']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def tasklist_list(self, **params) -> Optional[Dict[str, Any]]:
        """
        Query all robot task chains - Get list of all available task chains.
        
        Args:
            **params: Query parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.tasklist_list()
        """
        req_id, resp_id, desc = TASK_COMMANDS['tasklist_list']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def tasklist_name(self, **params) -> Optional[Dict[str, Any]]:
        """
        Execute pre-stored task chain - Run a named task chain.
        
        Args:
            **params: Execution parameters (to be specified)
                - Task chain name
                - Execution options
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.tasklist_name(name="delivery_task")
        """
        req_id, resp_id, desc = TASK_COMMANDS['tasklist_name']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def target_path(self, **params) -> Optional[Dict[str, Any]]:
        """
        Get path navigation path - Query the planned path.
        
        Args:
            **params: Query parameters (to be specified)
                - Start position
                - End position
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.target_path(start_x=0, start_y=0, end_x=1, end_y=1)
        """
        req_id, resp_id, desc = TASK_COMMANDS['target_path']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def cleartargetlist(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear specified navigation path - Remove specific path from queue.
        
        Args:
            **params: Clear parameters (to be specified)
                - Path identifier
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.cleartargetlist(path_id=123)
        """
        req_id, resp_id, desc = TASK_COMMANDS['cleartargetlist']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def safeclearmovements(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear specified navigation path by task id - Safely remove task.
        
        Args:
            **params: Clear parameters (to be specified)
                - Task ID
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.safeclearmovements(task_id=456)
        """
        req_id, resp_id, desc = TASK_COMMANDS['safeclearmovements']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    @staticmethod
    def get_available_commands() -> List[str]:
        """
        Get list of all available task commands.
        
        Returns:
            List of command name strings
        """
        return list(TASK_COMMANDS.keys())
    
    @staticmethod
    def get_command_info(command: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific command.
        
        Args:
            command: Command name string (e.g., 'gotarget', 'turn')
            
        Returns:
            Dictionary with command information:
            - request_id: Request message ID
            - response_id: Response message ID
            - description: Human-readable description
            Returns None if command not found
        """
        if command not in TASK_COMMANDS:
            return None
        
        req_id, resp_id, desc = TASK_COMMANDS[command]
        return {
            'request_id': req_id,
            'response_id': resp_id,
            'description': desc
        }


def main():
    """
    Interactive command-line interface for testing task commands.
    
    Allows entering commands like:
        turn angle=3.14 vw=1
        translate dist=0.5 vx=0.5 vy=0.5
        pause
        exit
    """
    from util import parse_command_line
    
    print("🤖 SEER Task Controller - Interactive Mode")
    print("=" * 60)
    
    # Create controller
    controller = SeerTaskController(robot_ip='192.168.1.123', robot_port=19206)
    print(f"Controller: {controller}")
    
    # Show available commands
    commands = controller.get_available_commands()
    print(f"\nAvailable commands ({len(commands)} total):")
    for cmd in commands:
        info = controller.get_command_info(cmd)
        print(f"  - {cmd:20s} : {info['description']}")
    
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
    print("  turn angle=3.14 vw=1")
    print("  translate dist=0.5 vx=0.5 vy=0.5")
    print("  turn angle=1.57 vw=-0.5 mode=1")
    print("  pause")
    print("  resume")
    print("  cancel")
    print("\nType 'exit' or 'quit' to disconnect and exit.")
    print("Type 'help' to show available commands.")
    print("-" * 60)
    
    try:
        while True:
            # Get user input
            try:
                line = input("\n🤖 > ").strip()
            except EOFError:
                print("\n")
                break
            
            if not line:
                continue
            
            # Check for exit commands
            if line.lower() in ['exit', 'quit', 'q']:
                print("👋 Exiting...")
                break
            
            # Check for help command
            if line.lower() == 'help':
                print("\nAvailable commands:")
                for cmd in commands:
                    info = controller.get_command_info(cmd)
                    print(f"  - {cmd:20s} : {info['description']}")
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
                print(f"� Calling {func_name}({', '.join(f'{k}={v}' for k, v in params.items())})")
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

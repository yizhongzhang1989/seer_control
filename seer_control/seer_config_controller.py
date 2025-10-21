#!/usr/bin/env python3
"""
SEER Robot Config Controller

This module provides configuration functions for SEER robots.
Each config command has its own dedicated function with specific parameters.

Features:
- Map management (upload, download, remove)
- Control lock (grab, release)
- Hardware configuration (ultrasonic, GNSS, motor, DI)
- Parameter management (set, save, reload)
- Calibration (motor, sensor data)
- Script management (upload, download, remove)
- Obstacle management (add, remove)
- Error management (set, clear)
- 3D tag mapping
- Joystick binding

Manual: https://seer-group.feishu.cn/wiki/WsI2wM46YiESh8k12EBclv23nOf?table=tblObW6PmjUPTyTn&view=vewiqqgyEX

Author: Assistant
Date: October 18, 2025
"""

from typing import Optional, Dict, Any, List
try:
    from .seer_controller_base import SeerControllerBase
except ImportError:
    from seer_controller_base import SeerControllerBase


# Config command IDs
# Format: (request_id, response_id, description)
CONFIG_COMMANDS = {
    'uploadmap': (4010, 14010, 'Upload map to robot'),
    'lock': (4005, 14005, 'Grab control lock'),
    'unlock': (4006, 14006, 'Release control lock'),
    'config_ultrasonic': (4130, 14130, 'Configure ultrasonic'),
    'clear_goodsshape': (4356, 14356, 'Clear goods shape'),
    'set_shelfshape': (4357, 14357, 'Set shelf description file'),
    'set_gnss_rover': (4462, 14462, 'Configure GNSS to Rover mode'),
    'set_gnss_baudrate': (4461, 14461, 'Configure GNSS default baudrate'),
    'send_canframe': (4400, 14400, 'Configure driver parameters'),
    'reset_gnss': (4460, 14460, 'Reset GNSS hardware configuration'),
    'removeobstacle': (4352, 14352, 'Remove dynamic obstacle'),
    'removemap': (4012, 14012, 'Delete map from robot'),
    'setparams': (4100, 14100, 'Temporarily modify robot parameters'),
    'saveparams': (4101, 14101, 'Permanently modify robot parameters'),
    'reloadparams': (4102, 14102, 'Restore robot parameters to default'),
    'config_push': (4091, 14091, 'Configure robot push port'),
    'motor_clear_fault': (4151, 14151, 'Motor clear fault'),
    'motor_calib': (4150, 14150, 'Motor calibration'),
    'upload_model': (4200, 14200, 'Upload model file to robot'),
    'downloadmap': (4011, 14011, 'Download map from robot'),
    'uploadscript': (4021, 14021, 'Upload robot script'),
    'downloadscript': (4022, 14022, 'Download robot script'),
    'removescript': (4023, 14023, 'Delete robot script'),
    'tagmapping_3d': (4353, 14353, '3D QR code mapping'),
    'config_di': (4140, 14140, 'Configure DI'),
    'calib_push_data': (4201, 14201, 'Set calibration process data'),
    'calib_confirm': (4202, 14202, 'Confirm calibration data'),
    'calib_clear': (4203, 14203, 'Clear calibration data by type'),
    'calib_clear_all': (4209, 14209, 'Clear robot.cp file'),
    'setwarning': (4802, 14802, 'Set third-party warning'),
    'clearwarning': (4803, 14803, 'Clear third-party warning'),
    'seterror': (4800, 14800, 'Set third-party error'),
    'clearallerrors': (4009, 14009, 'Clear all current robot errors'),
    'clear_odo': (4450, 14450, 'Reset runtime information'),
    'clearerror': (4801, 14801, 'Clear third-party error'),
    'addobstacle': (4350, 14350, 'Insert dynamic obstacle (robot coordinate)'),
    'addgobstacle': (4351, 14351, 'Insert dynamic obstacle (world coordinate)'),
    'joystick_bind_keymap': (4470, 14470, 'Upload joystick custom binding events'),
}


class SeerConfigController(SeerControllerBase):
    """
    SEER Robot Config Controller.
    
    Provides dedicated functions for each configuration command.
    Each command has specific parameters and JSON payload structure.
    
    Example:
        controller = SeerConfigController('192.168.192.5', 19207)
        controller.connect()
        
        # Grab control lock
        result = controller.lock()
        
        # Upload map
        result = controller.uploadmap(map_name="factory", map_data=...)
        
        # Configure parameters
        result = controller.setparams(param1=value1, param2=value2)
        
        # Release control lock
        result = controller.unlock()
        
        controller.disconnect()
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19207):
        """
        Initialize the config controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
            robot_port: Port number for config operations (default: 19207)
        """
        super().__init__(robot_ip, robot_port)
    
    def uploadmap(self, **params) -> Optional[Dict[str, Any]]:
        """
        Upload map to robot.
        
        Args:
            **params: Map upload parameters
                - map_name: Name of the map
                - map_data: Map file data
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.uploadmap(map_name="factory_floor1", map_data=...)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['uploadmap']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=30.0  # Longer timeout for file upload
        )
    
    def lock(self, **params) -> Optional[Dict[str, Any]]:
        """
        Grab control lock - Take exclusive control of the robot.
        
        Args:
            **params: Lock parameters (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.lock()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['lock']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def unlock(self, **params) -> Optional[Dict[str, Any]]:
        """
        Release control lock - Release exclusive control of the robot.
        
        Args:
            **params: Unlock parameters (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.unlock()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['unlock']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def config_ultrasonic(self, **params) -> Optional[Dict[str, Any]]:
        """
        Configure ultrasonic sensors.
        
        Args:
            **params: Ultrasonic configuration parameters
                - enable: Enable/disable ultrasonic
                - sensitivity: Sensor sensitivity
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.config_ultrasonic(enable=True, sensitivity=0.5)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['config_ultrasonic']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clear_goodsshape(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear goods shape configuration.
        
        Args:
            **params: Clear parameters (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clear_goodsshape()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['clear_goodsshape']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def set_shelfshape(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set shelf description file.
        
        Args:
            **params: Shelf shape parameters
                - shelf_config: Shelf configuration data
                - dimensions: Shelf dimensions
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.set_shelfshape(shelf_config=...)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['set_shelfshape']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def set_gnss_rover(self, **params) -> Optional[Dict[str, Any]]:
        """
        Configure GNSS to Rover mode.
        
        Args:
            **params: GNSS Rover configuration parameters
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.set_gnss_rover()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['set_gnss_rover']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def set_gnss_baudrate(self, **params) -> Optional[Dict[str, Any]]:
        """
        Configure GNSS default baudrate.
        
        Args:
            **params: GNSS baudrate parameters
                - baudrate: Baudrate value (e.g., 9600, 115200)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.set_gnss_baudrate(baudrate=115200)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['set_gnss_baudrate']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def send_canframe(self, **params) -> Optional[Dict[str, Any]]:
        """
        Configure driver parameters via CAN frame.
        
        Args:
            **params: CAN frame parameters
                - can_id: CAN identifier
                - data: CAN data bytes
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.send_canframe(can_id=0x123, data=[0x01, 0x02])
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['send_canframe']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def reset_gnss(self, **params) -> Optional[Dict[str, Any]]:
        """
        Reset GNSS hardware configuration.
        
        Args:
            **params: Reset parameters (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.reset_gnss()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['reset_gnss']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def removeobstacle(self, **params) -> Optional[Dict[str, Any]]:
        """
        Remove dynamic obstacle.
        
        Args:
            **params: Obstacle removal parameters
                - obstacle_id: ID of obstacle to remove
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.removeobstacle(obstacle_id=123)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['removeobstacle']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def removemap(self, **params) -> Optional[Dict[str, Any]]:
        """
        Delete map from robot.
        
        Args:
            **params: Map removal parameters
                - map_name: Name of map to delete
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.removemap(map_name="old_factory_map")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['removemap']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def setparams(self, **params) -> Optional[Dict[str, Any]]:
        """
        Temporarily modify robot parameters (not saved to disk).
        
        Args:
            **params: Parameter key-value pairs to set
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.setparams(max_speed=1.5, acceleration=0.5)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['setparams']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def saveparams(self, **params) -> Optional[Dict[str, Any]]:
        """
        Permanently modify robot parameters (saved to disk).
        
        Args:
            **params: Parameter key-value pairs to save
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.saveparams(max_speed=1.5, acceleration=0.5)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['saveparams']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def reloadparams(self, **params) -> Optional[Dict[str, Any]]:
        """
        Restore robot parameters to default values.
        
        Args:
            **params: Reload parameters (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.reloadparams()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['reloadparams']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def config_push(self, **params) -> Optional[Dict[str, Any]]:
        """
        Configure robot push port for real-time data updates.
        
        Args:
            **params: Push configuration parameters
                - port: Port number for push updates
                - frequency: Update frequency
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.config_push(port=19999, frequency=10)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['config_push']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def motor_clear_fault(self, **params) -> Optional[Dict[str, Any]]:
        """
        Motor clear fault - Reset motor error state.
        
        Args:
            **params: Motor fault clear parameters
                - motor_id: Specific motor ID (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.motor_clear_fault()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['motor_clear_fault']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def motor_calib(self, **params) -> Optional[Dict[str, Any]]:
        """
        Motor calibration - Set motor zero position.
        
        Args:
            **params: Motor calibration parameters
                - motor_id: Specific motor ID (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.motor_calib()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['motor_calib']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def upload_model(self, **params) -> Optional[Dict[str, Any]]:
        """
        Upload model file to robot.
        
        Args:
            **params: Model upload parameters
                - model_name: Name of the model
                - model_data: Model file data
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.upload_model(model_name="detection_model", model_data=...)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['upload_model']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=60.0  # Longer timeout for model upload
        )
    
    def downloadmap(self, **params) -> Optional[Dict[str, Any]]:
        """
        Download map from robot.
        
        Args:
            **params: Map download parameters
                - map_name: Name of map to download
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.downloadmap(map_name="factory_floor1")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['downloadmap']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=30.0  # Longer timeout for file download
        )
    
    def uploadscript(self, **params) -> Optional[Dict[str, Any]]:
        """
        Upload robot script.
        
        Args:
            **params: Script upload parameters
                - script_name: Name of the script
                - script_data: Script file data/content
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.uploadscript(script_name="startup.py", script_data=...)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['uploadscript']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=30.0  # Longer timeout for file upload
        )
    
    def downloadscript(self, **params) -> Optional[Dict[str, Any]]:
        """
        Download robot script.
        
        Args:
            **params: Script download parameters
                - script_name: Name of script to download
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.downloadscript(script_name="startup.py")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['downloadscript']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=30.0  # Longer timeout for file download
        )
    
    def removescript(self, **params) -> Optional[Dict[str, Any]]:
        """
        Delete robot script.
        
        Args:
            **params: Script removal parameters
                - script_name: Name of script to delete
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.removescript(script_name="old_script.py")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['removescript']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def tagmapping_3d(self, **params) -> Optional[Dict[str, Any]]:
        """
        3D QR code mapping - Create map using 3D QR codes.
        
        Args:
            **params: 3D tag mapping parameters
                - mapping_mode: Mapping mode
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.tagmapping_3d(mapping_mode=1)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['tagmapping_3d']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def config_di(self, **params) -> Optional[Dict[str, Any]]:
        """
        Configure DI (Digital Input).
        
        Args:
            **params: DI configuration parameters
                - di_id: Digital input ID
                - mode: Input mode
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.config_di(di_id=1, mode="normal")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['config_di']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def calib_push_data(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set calibration process data.
        
        Args:
            **params: Calibration data parameters
                - calib_type: Type of calibration
                - data: Calibration data
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.calib_push_data(calib_type="camera", data=...)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['calib_push_data']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def calib_confirm(self, **params) -> Optional[Dict[str, Any]]:
        """
        Confirm calibration data.
        
        Args:
            **params: Calibration confirmation parameters
                - calib_type: Type of calibration to confirm
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.calib_confirm(calib_type="camera")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['calib_confirm']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def calib_clear(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear calibration data by type.
        
        Args:
            **params: Calibration clear parameters
                - calib_type: Type of calibration to clear
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.calib_clear(calib_type="camera")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['calib_clear']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def calib_clear_all(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear robot.cp file - Remove all calibration data.
        
        Args:
            **params: Clear all parameters (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.calib_clear_all()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['calib_clear_all']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def setwarning(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set third-party warning.
        
        Args:
            **params: Warning parameters
                - warning_code: Warning code
                - warning_msg: Warning message
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.setwarning(warning_code=100, warning_msg="Custom warning")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['setwarning']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clearwarning(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear third-party warning.
        
        Args:
            **params: Warning clear parameters
                - warning_code: Warning code to clear
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clearwarning(warning_code=100)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['clearwarning']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def seterror(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set third-party error.
        
        Args:
            **params: Error parameters
                - error_code: Error code
                - error_msg: Error message
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.seterror(error_code=500, error_msg="Custom error")
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['seterror']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clearallerrors(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear all current robot errors.
        
        Args:
            **params: Clear all errors parameters (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clearallerrors()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['clearallerrors']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clear_odo(self, **params) -> Optional[Dict[str, Any]]:
        """
        Reset runtime information (odometry).
        
        Args:
            **params: Reset parameters (if any)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clear_odo()
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['clear_odo']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clearerror(self, **params) -> Optional[Dict[str, Any]]:
        """
        Clear third-party error.
        
        Args:
            **params: Error clear parameters
                - error_code: Error code to clear
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clearerror(error_code=500)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['clearerror']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def addobstacle(self, **params) -> Optional[Dict[str, Any]]:
        """
        Insert dynamic obstacle in robot coordinate system.
        
        Args:
            **params: Obstacle parameters
                - x: X coordinate in robot frame
                - y: Y coordinate in robot frame
                - width: Obstacle width
                - height: Obstacle height
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.addobstacle(x=1.0, y=0.5, width=0.3, height=0.3)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['addobstacle']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def addgobstacle(self, **params) -> Optional[Dict[str, Any]]:
        """
        Insert dynamic obstacle in world coordinate system.
        
        Args:
            **params: Obstacle parameters
                - x: X coordinate in world frame
                - y: Y coordinate in world frame
                - width: Obstacle width
                - height: Obstacle height
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.addgobstacle(x=5.0, y=3.0, width=0.5, height=0.5)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['addgobstacle']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def joystick_bind_keymap(self, **params) -> Optional[Dict[str, Any]]:
        """
        Upload joystick custom binding events.
        
        Args:
            **params: Joystick binding parameters
                - keymap: Key mapping configuration
                - bindings: Event bindings
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.joystick_bind_keymap(keymap=...)
        """
        req_id, resp_id, desc = CONFIG_COMMANDS['joystick_bind_keymap']
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
        Get list of all available config commands.
        
        Returns:
            List of command name strings
        """
        return list(CONFIG_COMMANDS.keys())
    
    @staticmethod
    def get_command_info(command: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific command.
        
        Args:
            command: Command name string (e.g., 'lock', 'uploadmap')
            
        Returns:
            Dictionary with command information:
            - request_id: Request message ID
            - response_id: Response message ID
            - description: Human-readable description
            Returns None if command not found
        """
        if command not in CONFIG_COMMANDS:
            return None
        
        req_id, resp_id, desc = CONFIG_COMMANDS[command]
        return {
            'request_id': req_id,
            'response_id': resp_id,
            'description': desc
        }


def main():
    """
    Interactive command-line interface for testing config commands.
    
    Allows entering commands like:
        lock
        setparams max_speed=1.5
        unlock
        exit
    """
    from util import parse_command_line
    
    print("🔧 SEER Config Controller - Interactive Mode")
    print("=" * 60)
    
    # Create controller
    controller = SeerConfigController(robot_ip='192.168.1.123', robot_port=19207)
    print(f"Controller: {controller}")
    
    # Show available commands
    commands = controller.get_available_commands()
    print(f"\nAvailable commands ({len(commands)} total):")
    print("\nMap Management:")
    for cmd in ['uploadmap', 'downloadmap', 'removemap']:
        info = controller.get_command_info(cmd)
        print(f"  - {cmd:25s} : {info['description']}")
    
    print("\nControl Lock:")
    for cmd in ['lock', 'unlock']:
        info = controller.get_command_info(cmd)
        print(f"  - {cmd:25s} : {info['description']}")
    
    print("\nParameters:")
    for cmd in ['setparams', 'saveparams', 'reloadparams']:
        info = controller.get_command_info(cmd)
        print(f"  - {cmd:25s} : {info['description']}")
    
    print("\nMotor:")
    for cmd in ['motor_clear_fault', 'motor_calib']:
        info = controller.get_command_info(cmd)
        print(f"  - {cmd:25s} : {info['description']}")
    
    print("\nErrors:")
    for cmd in ['seterror', 'clearerror', 'clearallerrors', 'setwarning', 'clearwarning']:
        info = controller.get_command_info(cmd)
        print(f"  - {cmd:25s} : {info['description']}")
    
    print(f"\n... and {len(commands) - 17} more commands (type 'help' to see all)")
    
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
    print("  lock")
    print("  setparams max_speed=1.5 acceleration=0.5")
    print("  unlock")
    print("  addobstacle x=1.0 y=0.5 width=0.3 height=0.3")
    print("\nType 'exit' or 'quit' to disconnect and exit.")
    print("Type 'help' to show all available commands.")
    print("-" * 60)
    
    try:
        while True:
            # Get user input
            try:
                line = input("\n🔧 > ").strip()
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
                print("\nAll available commands:")
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

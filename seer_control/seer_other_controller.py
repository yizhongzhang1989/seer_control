#!/usr/bin/env python3
"""
SEER Robot Other Controller

This module provides miscellaneous control functions for SEER robots.
Each control command has its own dedicated function with specific parameters.

Features:
- Audio management (play, pause, resume, stop, upload, download, list)
- Digital I/O control (DO, DI, relay, charging relay)
- Roller/belt control (load, unload, roll in all directions)
- Jack mechanism control (load, unload, stop, set height)
- Fork control (stop, set height)
- Hook control (load, unload)
- Motor control (enable, disable, soft emergency stop)
- Cargo status management (reset, bind, unbind)
- Calibration (start, cancel, result, visualization)
- SLAM (start, stop scanning)
- Data management (modbus, peripheral, transparent)
- Bin detection
- Replay

Control commands (55 total):
- Audio: play_audio, pause_audio, resume_audio, stop_audio, upload_audio, 
         download_audio, audio_list
- I/O: setdo, setdos, setvdi, setrelay, setchargingrelay
- Roller: roller_front_roll, roller_back_roll, roller_left_roll, roller_right_roll,
          roller_front_load, roller_front_pre_load, roller_front_unload,
          roller_back_load, roller_back_pre_load, roller_back_unload,
          roller_left_load, roller_left_pre_load, roller_left_unload,
          roller_right_load, roller_right_pre_load, roller_right_unload,
          roller_front_back_inverse, roller_left_right_inverse, roller_stop
- Jack: jack_load, jack_unload, jack_stop, jack_set_height
- Fork: stop_fork, set_fork_height
- Hook: hook_load, hook_unload
- Motor: set_motor_enable, softemc
- Cargo: reset_cargo, set_container_goods, clear_goods, clear_container, 
         clear_all_containers_goods
- Calibration: calibrate, endcalibrate, calib_result, calib_allinone2
- SLAM: slam, endslam
- Data: set_modbus, write_peripheral_data, update_transparent_data
- Detection: bin_detect
- Replay: replay

Manual: https://seer-group.feishu.cn/wiki/WsI2wM46YiESh8k12EBclv23nOf?table=tblObW6PmjUPTyTn&view=vewiqqgyEX

Author: Assistant
Date: October 18, 2025
"""

from typing import Optional, Dict, Any, List
from .seer_controller_base import SeerControllerBase


# Other control command IDs
# Format: (request_id, response_id, description)
OTHER_COMMANDS = {
    # Audio commands
    'play_audio': (6000, 16000, 'Play audio file'),
    'pause_audio': (6010, 16010, 'Pause playing audio'),
    'resume_audio': (6011, 16011, 'Resume playing audio'),
    'stop_audio': (6012, 16012, 'Stop playing audio'),
    'upload_audio': (6030, 16030, 'Upload audio file'),
    'download_audio': (6031, 16031, 'Download audio file'),
    'audio_list': (6033, 16033, 'Get audio file list'),
    
    # Digital I/O commands
    'setdo': (6001, 16001, 'Set DO'),
    'setdos': (6002, 16002, 'Batch set DO'),
    'setvdi': (6020, 16020, 'Set virtual DI'),
    'setrelay': (6003, 16003, 'Set relay'),
    'setchargingrelay': (6005, 16005, 'Set charging relay'),
    
    # Motor commands
    'set_motor_enable': (6201, 16201, 'Motor enable/disable'),
    'softemc': (6004, 16004, 'Soft emergency stop'),
    
    # Roller/belt commands - Front
    'roller_front_roll': (6051, 16051, 'Roller/belt roll forward'),
    'roller_front_load': (6055, 16055, 'Roller/belt front load'),
    'roller_front_pre_load': (6057, 16057, 'Roller/belt front pre-load'),
    'roller_front_unload': (6056, 16056, 'Roller/belt front unload'),
    
    # Roller/belt commands - Back
    'roller_back_roll': (6052, 16052, 'Roller/belt roll backward'),
    'roller_back_load': (6058, 16058, 'Roller/belt back load'),
    'roller_back_pre_load': (6060, 16060, 'Roller/belt back pre-load'),
    'roller_back_unload': (6059, 16059, 'Roller/belt back unload'),
    
    # Roller/belt commands - Left
    'roller_left_roll': (6053, 16053, 'Roller/belt roll left'),
    'roller_left_load': (6061, 16061, 'Roller/belt left load'),
    'roller_left_pre_load': (6065, 16065, 'Roller/belt left pre-load'),
    'roller_left_unload': (6062, 16062, 'Roller/belt left unload'),
    
    # Roller/belt commands - Right
    'roller_right_roll': (6054, 16054, 'Roller/belt roll right'),
    'roller_right_load': (6063, 16063, 'Roller/belt right load'),
    'roller_right_pre_load': (6066, 16066, 'Roller/belt right pre-load'),
    'roller_right_unload': (6064, 16064, 'Roller/belt right unload'),
    
    # Roller/belt commands - Other
    'roller_front_back_inverse': (6069, 16069, 'Roller/belt front-back inverse'),
    'roller_left_right_inverse': (6068, 16068, 'Roller/belt left-right inverse'),
    'roller_stop': (6067, 16067, 'Roller/belt stop'),
    
    # Jack mechanism commands
    'jack_load': (6070, 16070, 'Jack mechanism rise'),
    'jack_unload': (6071, 16071, 'Jack mechanism descend'),
    'jack_stop': (6072, 16072, 'Jack mechanism stop'),
    'jack_set_height': (6073, 16073, 'Jack set height'),
    
    # Fork commands
    'stop_fork': (6041, 16041, 'Stop fork'),
    'set_fork_height': (6040, 16040, 'Set fork height'),
    
    # Hook commands
    'hook_load': (6082, 16082, 'Hook load'),
    'hook_unload': (6083, 16083, 'Hook unload'),
    
    # Cargo status commands
    'reset_cargo': (6080, 16080, 'Clear cargo status'),
    'set_container_goods': (6804, 16804, 'Bind goods to container'),
    'clear_goods': (6801, 16801, 'Unbind specified goods'),
    'clear_container': (6802, 16802, 'Unbind goods from specified container'),
    'clear_all_containers_goods': (6803, 16803, 'Unbind goods from all containers'),
    
    # Calibration commands
    'calibrate': (6110, 16110, 'Start calibration'),
    'endcalibrate': (6111, 16111, 'Cancel calibration'),
    'calib_result': (6112, 16112, 'Get current calibration result'),
    'calib_allinone2': (6115, 16115, 'Calibration process visualization'),
    
    # SLAM commands
    'slam': (6100, 16100, 'Start scanning map'),
    'endslam': (6101, 16101, 'Stop scanning map'),
    
    # Data commands
    'set_modbus': (6086, 16086, 'Write modbus data'),
    'write_peripheral_data': (6049, 16049, 'Write peripheral user-defined data'),
    'update_transparent_data': (6900, 16900, 'Update transparent data'),
    
    # Detection commands
    'bin_detect': (6901, 16901, 'Bin detection'),
    
    # Replay commands
    'replay': (6910, 16910, 'Replay'),
}


class SeerOtherController(SeerControllerBase):
    """
    SEER Robot Other Controller.
    
    Provides dedicated functions for miscellaneous control commands.
    Each command has specific parameters and JSON payload structure.
    
    Example:
        controller = SeerOtherController('192.168.192.5', 19210)
        controller.connect()
        
        # Play audio
        result = controller.play_audio(audio_file="welcome.mp3")
        
        # Set DO
        result = controller.setdo(index=1, value=1)
        
        # Jack load
        result = controller.jack_load()
        
        controller.disconnect()
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19210):
        """
        Initialize the other controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
            robot_port: Port number for other commands (default: 19210)
        """
        super().__init__(robot_ip, robot_port)
    
    # ========== Audio Commands ==========
    
    def play_audio(self, **params) -> Optional[Dict[str, Any]]:
        """
        Play audio file - Play specified audio file.
        
        Args:
            **params: Audio playback parameters (to be specified)
                - audio_file: Name of audio file to play
                - volume: Volume level
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.play_audio(audio_file="welcome.mp3")
        """
        req_id, resp_id, desc = OTHER_COMMANDS['play_audio']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def pause_audio(self) -> Optional[Dict[str, Any]]:
        """
        Pause playing audio - Pause current audio playback.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.pause_audio()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['pause_audio']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def resume_audio(self) -> Optional[Dict[str, Any]]:
        """
        Resume playing audio - Resume paused audio playback.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.resume_audio()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['resume_audio']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def stop_audio(self) -> Optional[Dict[str, Any]]:
        """
        Stop playing audio - Stop current audio playback.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.stop_audio()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['stop_audio']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def upload_audio(self, **params) -> Optional[Dict[str, Any]]:
        """
        Upload audio file - Upload audio file to robot.
        
        Args:
            **params: Upload parameters (to be specified)
                - audio_file: Name of audio file
                - audio_data: Audio file data
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.upload_audio(audio_file="alert.mp3", audio_data=...)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['upload_audio']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=30.0  # Longer timeout for upload
        )
    
    def download_audio(self, **params) -> Optional[Dict[str, Any]]:
        """
        Download audio file - Download audio file from robot.
        
        Args:
            **params: Download parameters (to be specified)
                - audio_file: Name of audio file to download
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.download_audio(audio_file="welcome.mp3")
        """
        req_id, resp_id, desc = OTHER_COMMANDS['download_audio']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=30.0  # Longer timeout for download
        )
    
    def audio_list(self) -> Optional[Dict[str, Any]]:
        """
        Get audio file list - Get list of all audio files on robot.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.audio_list()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['audio_list']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Digital I/O Commands ==========
    
    def setdo(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set DO - Set digital output.
        
        Args:
            **params: DO parameters (to be specified)
                - index: DO index
                - value: DO value (0 or 1)
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.setdo(index=1, value=1)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['setdo']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def setdos(self, **params) -> Optional[Dict[str, Any]]:
        """
        Batch set DO - Set multiple digital outputs.
        
        Args:
            **params: Batch DO parameters (to be specified)
                - values: List of DO values
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.setdos(values=[1, 0, 1, 1])
        """
        req_id, resp_id, desc = OTHER_COMMANDS['setdos']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def setvdi(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set virtual DI - Set virtual digital input.
        
        Args:
            **params: Virtual DI parameters (to be specified)
                - index: Virtual DI index
                - value: Virtual DI value (0 or 1)
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.setvdi(index=1, value=1)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['setvdi']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def setrelay(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set relay - Set relay state.
        
        Args:
            **params: Relay parameters (to be specified)
                - index: Relay index
                - value: Relay value (0 or 1)
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.setrelay(index=1, value=1)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['setrelay']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def setchargingrelay(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set charging relay - Set charging relay state.
        
        Args:
            **params: Charging relay parameters (to be specified)
                - value: Relay value (0 or 1)
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.setchargingrelay(value=1)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['setchargingrelay']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Motor Commands ==========
    
    def set_motor_enable(self, **params) -> Optional[Dict[str, Any]]:
        """
        Motor enable/disable - Enable or disable motor.
        
        Args:
            **params: Motor enable parameters (to be specified)
                - enable: Enable (1) or disable (0)
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.set_motor_enable(enable=1)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['set_motor_enable']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def softemc(self) -> Optional[Dict[str, Any]]:
        """
        Soft emergency stop - Trigger soft emergency stop.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.softemc()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['softemc']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Roller/Belt Commands ==========
    
    def roller_front_roll(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt roll forward - Roll roller/belt forward.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_front_roll()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_front_roll']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_front_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt front load - Load from front.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_front_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_front_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_front_pre_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt front pre-load - Pre-load from front.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_front_pre_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_front_pre_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_front_unload(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt front unload - Unload to front.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_front_unload()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_front_unload']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_back_roll(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt roll backward - Roll roller/belt backward.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_back_roll()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_back_roll']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_back_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt back load - Load from back.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_back_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_back_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_back_pre_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt back pre-load - Pre-load from back.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_back_pre_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_back_pre_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_back_unload(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt back unload - Unload to back.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_back_unload()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_back_unload']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_left_roll(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt roll left - Roll roller/belt left.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_left_roll()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_left_roll']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_left_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt left load - Load from left.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_left_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_left_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_left_pre_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt left pre-load - Pre-load from left.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_left_pre_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_left_pre_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_left_unload(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt left unload - Unload to left.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_left_unload()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_left_unload']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_right_roll(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt roll right - Roll roller/belt right.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_right_roll()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_right_roll']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_right_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt right load - Load from right.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_right_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_right_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_right_pre_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt right pre-load - Pre-load from right.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_right_pre_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_right_pre_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_right_unload(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt right unload - Unload to right.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_right_unload()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_right_unload']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_front_back_inverse(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt front-back inverse - Inverse front and back roller direction.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_front_back_inverse()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_front_back_inverse']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_left_right_inverse(self, **params) -> Optional[Dict[str, Any]]:
        """
        Roller/belt left-right inverse - Inverse left and right roller direction.
        
        Args:
            **params: Roller parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_left_right_inverse()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_left_right_inverse']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def roller_stop(self) -> Optional[Dict[str, Any]]:
        """
        Roller/belt stop - Stop roller/belt movement.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.roller_stop()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['roller_stop']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Jack Mechanism Commands ==========
    
    def jack_load(self) -> Optional[Dict[str, Any]]:
        """
        Jack mechanism rise - Raise jack mechanism.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.jack_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['jack_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def jack_unload(self) -> Optional[Dict[str, Any]]:
        """
        Jack mechanism descend - Lower jack mechanism.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.jack_unload()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['jack_unload']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def jack_stop(self) -> Optional[Dict[str, Any]]:
        """
        Jack mechanism stop - Stop jack mechanism.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.jack_stop()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['jack_stop']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def jack_set_height(self, height: float) -> Optional[Dict[str, Any]]:
        """
        Jack set height - Set jack to specific height.
        
        Args:
            height: Jack height in meters (顶升的高度, 单位 m)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.jack_set_height(height=0.5)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['jack_set_height']
        
        payload = {
            'height': height
        }
        
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=payload,
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Fork Commands ==========
    
    def stop_fork(self) -> Optional[Dict[str, Any]]:
        """
        Stop fork - Stop fork movement.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.stop_fork()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['stop_fork']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def set_fork_height(self, **params) -> Optional[Dict[str, Any]]:
        """
        Set fork height - Set fork to specific height.
        
        Args:
            **params: Fork height parameters (to be specified)
                - height: Target height
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.set_fork_height(height=0.5)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['set_fork_height']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Hook Commands ==========
    
    def hook_load(self, **params) -> Optional[Dict[str, Any]]:
        """
        Hook load - Load with hook.
        
        Args:
            **params: Hook parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.hook_load()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['hook_load']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def hook_unload(self, **params) -> Optional[Dict[str, Any]]:
        """
        Hook unload - Unload with hook.
        
        Args:
            **params: Hook parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.hook_unload()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['hook_unload']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Cargo Status Commands ==========
    
    def reset_cargo(self) -> Optional[Dict[str, Any]]:
        """
        Clear cargo status - Reset cargo status.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.reset_cargo()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['reset_cargo']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def set_container_goods(self, **params) -> Optional[Dict[str, Any]]:
        """
        Bind goods to container - Associate goods with container.
        
        Args:
            **params: Binding parameters (to be specified)
                - container_id: Container identifier
                - goods_id: Goods identifier
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.set_container_goods(container_id="C1", goods_id="G1")
        """
        req_id, resp_id, desc = OTHER_COMMANDS['set_container_goods']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clear_goods(self, **params) -> Optional[Dict[str, Any]]:
        """
        Unbind specified goods - Remove goods binding.
        
        Args:
            **params: Unbinding parameters (to be specified)
                - goods_id: Goods identifier
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clear_goods(goods_id="G1")
        """
        req_id, resp_id, desc = OTHER_COMMANDS['clear_goods']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clear_container(self, **params) -> Optional[Dict[str, Any]]:
        """
        Unbind goods from specified container - Remove all goods from container.
        
        Args:
            **params: Unbinding parameters (to be specified)
                - container_id: Container identifier
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clear_container(container_id="C1")
        """
        req_id, resp_id, desc = OTHER_COMMANDS['clear_container']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def clear_all_containers_goods(self) -> Optional[Dict[str, Any]]:
        """
        Unbind goods from all containers - Remove all goods bindings.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.clear_all_containers_goods()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['clear_all_containers_goods']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Calibration Commands ==========
    
    def calibrate(self, **params) -> Optional[Dict[str, Any]]:
        """
        Start calibration - Begin calibration process.
        
        Args:
            **params: Calibration parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.calibrate()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['calibrate']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def endcalibrate(self) -> Optional[Dict[str, Any]]:
        """
        Cancel calibration - Stop calibration process.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.endcalibrate()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['endcalibrate']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def calib_result(self) -> Optional[Dict[str, Any]]:
        """
        Get current calibration result - Query calibration result.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.calib_result()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['calib_result']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    def calib_allinone2(self, **params) -> Optional[Dict[str, Any]]:
        """
        Calibration process visualization - Visualize calibration process.
        
        Args:
            **params: Visualization parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.calib_allinone2()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['calib_allinone2']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    # ========== SLAM Commands ==========
    
    def slam(self, **params) -> Optional[Dict[str, Any]]:
        """
        Start scanning map - Begin SLAM process.
        
        Args:
            **params: SLAM parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.slam()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['slam']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    def endslam(self) -> Optional[Dict[str, Any]]:
        """
        Stop scanning map - End SLAM process.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.endslam()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['endslam']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg={},  # Empty payload
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Data Commands ==========
    
    def set_modbus(self, **params) -> Optional[Dict[str, Any]]:
        """
        Write modbus data - Write data to modbus.
        
        Args:
            **params: Modbus parameters (to be specified)
                - address: Modbus address
                - value: Data value
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.set_modbus(address=100, value=123)
        """
        req_id, resp_id, desc = OTHER_COMMANDS['set_modbus']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def write_peripheral_data(self, **params) -> Optional[Dict[str, Any]]:
        """
        Write peripheral user-defined data - Write custom data to peripheral.
        
        Args:
            **params: Peripheral data parameters (to be specified)
                - data: User-defined data
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.write_peripheral_data(data="custom_data")
        """
        req_id, resp_id, desc = OTHER_COMMANDS['write_peripheral_data']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    def update_transparent_data(self, **params) -> Optional[Dict[str, Any]]:
        """
        Update transparent data - Update transparent transmission data.
        
        Args:
            **params: Transparent data parameters (to be specified)
                - data: Transparent data
                - etc.
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.update_transparent_data(data="transparent_data")
        """
        req_id, resp_id, desc = OTHER_COMMANDS['update_transparent_data']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=5.0
        )
    
    # ========== Detection Commands ==========
    
    def bin_detect(self, **params) -> Optional[Dict[str, Any]]:
        """
        Bin detection - Detect bin/storage location.
        
        Args:
            **params: Detection parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.bin_detect()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['bin_detect']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    # ========== Replay Commands ==========
    
    def replay(self, **params) -> Optional[Dict[str, Any]]:
        """
        Replay - Replay recorded actions.
        
        Args:
            **params: Replay parameters (to be specified)
        
        Returns:
            Response dictionary if successful, None if failed
            
        Example:
            result = controller.replay()
        """
        req_id, resp_id, desc = OTHER_COMMANDS['replay']
        return self.send_command(
            req_id=1,
            msg_type=req_id,
            msg=params,
            expected_response=resp_id,
            timeout=10.0
        )
    
    # ========== Helper Methods ==========
    
    @staticmethod
    def get_available_commands() -> List[str]:
        """
        Get list of all available other commands.
        
        Returns:
            List of command name strings
        """
        return list(OTHER_COMMANDS.keys())
    
    @staticmethod
    def get_command_info(command: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific command.
        
        Args:
            command: Command name string (e.g., 'play_audio', 'jack_load')
            
        Returns:
            Dictionary with command information:
            - request_id: Request message ID
            - response_id: Response message ID
            - description: Human-readable description
            Returns None if command not found
        """
        if command not in OTHER_COMMANDS:
            return None
        
        req_id, resp_id, desc = OTHER_COMMANDS[command]
        return {
            'request_id': req_id,
            'response_id': resp_id,
            'description': desc
        }


def main():
    """
    Interactive command-line interface for testing other commands.
    
    Allows entering commands like:
        play_audio audio_file=welcome.mp3
        setdo index=1 value=1
        jack_load
        roller_stop
        exit
    """
    from util import parse_command_line
    
    print("🤖 SEER Other Controller - Interactive Mode")
    print("=" * 60)
    
    # Create controller
    controller = SeerOtherController(robot_ip='192.168.1.123', robot_port=19210)
    print(f"Controller: {controller}")
    
    # Show available commands
    commands = controller.get_available_commands()
    print(f"\nAvailable commands ({len(commands)} total):")
    
    # Group commands by category
    categories = {
        'Audio': ['play_audio', 'pause_audio', 'resume_audio', 'stop_audio', 
                  'upload_audio', 'download_audio', 'audio_list'],
        'Digital I/O': ['setdo', 'setdos', 'setvdi', 'setrelay', 'setchargingrelay'],
        'Motor': ['set_motor_enable', 'softemc'],
        'Roller/Belt': [cmd for cmd in commands if cmd.startswith('roller_')],
        'Jack': [cmd for cmd in commands if cmd.startswith('jack_')],
        'Fork': ['stop_fork', 'set_fork_height'],
        'Hook': ['hook_load', 'hook_unload'],
        'Cargo': ['reset_cargo', 'set_container_goods', 'clear_goods', 
                  'clear_container', 'clear_all_containers_goods'],
        'Calibration': ['calibrate', 'endcalibrate', 'calib_result', 'calib_allinone2'],
        'SLAM': ['slam', 'endslam'],
        'Data': ['set_modbus', 'write_peripheral_data', 'update_transparent_data'],
        'Detection': ['bin_detect'],
        'Replay': ['replay'],
    }
    
    for category, category_cmds in categories.items():
        if category_cmds:
            print(f"\n  {category}:")
            for cmd in category_cmds:
                info = controller.get_command_info(cmd)
                if info:
                    print(f"    - {cmd:30s} : {info['description']}")
    
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
    print("  play_audio audio_file=welcome.mp3")
    print("  setdo index=1 value=1")
    print("  jack_load")
    print("  roller_stop")
    print("  reset_cargo")
    print("\nType 'exit' or 'quit' to disconnect and exit.")
    print("Type 'help' to show available commands.")
    print("-" * 60)
    
    try:
        while True:
            # Get user input
            try:
                line = input("\n🎛️  > ").strip()
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
                print("\nAvailable commands by category:")
                for category, category_cmds in categories.items():
                    if category_cmds:
                        print(f"\n  {category}:")
                        for cmd in category_cmds:
                            info = controller.get_command_info(cmd)
                            if info:
                                print(f"    - {cmd:30s} : {info['description']}")
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

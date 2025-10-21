#!/usr/bin/env python3
"""
SEER Control - Robot Controller Package

A comprehensive Python package for controlling SEER robots, providing access to:
- Status queries (65+ commands on port 19204)
- Task/Motion control (16 commands on port 19206)
- Control operations (9 commands on port 19205)
- Configuration (38 commands on port 19207)
- Other operations (55 commands on port 19210)
- Push data monitoring (port 19301)

Usage:
    from seer_control import SeerController
    
    robot = SeerController('192.168.1.123')
    robot.connect_essential()
    
    # Query status
    position = robot.status.query_status('loc')
    battery = robot.status.query_status('battery')
    
    # Control movement
    robot.task.gotarget(id="Station1")
    robot.control.pause()
    robot.control.resume()
    
    robot.disconnect_all()

Author: Assistant
Date: October 21, 2025
"""

from .seer_controller import SeerController
from .seer_status_controller import SeerStatusController
from .seer_task_controller import SeerTaskController
from .seer_control_controller import SeerControlController
from .seer_config_controller import SeerConfigController
from .seer_other_controller import SeerOtherController
from .seer_push_controller import SeerPushController
from .util import parse_command_line

__version__ = "1.0.0"
__all__ = [
    "SeerController",
    "SeerStatusController",
    "SeerTaskController",
    "SeerControlController",
    "SeerConfigController",
    "SeerOtherController",
    "SeerPushController",
    "parse_command_line",
]

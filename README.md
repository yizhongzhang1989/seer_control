# SEER Control

A comprehensive Python package for controlling SEER robots.

## Features

This package provides complete control over SEER robots through multiple specialized controllers:

- **Status Controller** (port 19204): 65+ query commands for robot status
- **Task Controller** (port 19206): 16 motion and navigation commands
- **Control Controller** (port 19205): 9 robot control operations
- **Config Controller** (port 19207): 38 configuration commands
- **Other Controller** (port 19210): 55 specialized operations (jack, RFID, etc.)
- **Push Controller** (port 19301): Real-time push data monitoring

## Installation

Clone this repository and install it as a package:

```bash
git clone <repository-url>
cd seer_control
pip install -e .
```

Or add the repository directory to your Python path.

## Quick Start

### Basic Usage

```python
from seer_control import SeerController

# Connect to robot
robot = SeerController('192.168.1.123')
robot.connect_essential()

# Query robot position
position = robot.status.query_status('loc')
print(f"Position: x={position['x']}, y={position['y']}, angle={position['angle']}")

# Query battery level
battery = robot.status.query_status('battery')
print(f"Battery: {battery['battery']}%")

# Navigate to a station
robot.task.gotarget(id="Station1")

# Control robot
robot.control.pause()
robot.control.resume()

# Disconnect when done
robot.disconnect_all()
```

### Advanced Navigation

```python
from seer_control import SeerController

robot = SeerController('192.168.1.123')
robot.connect_essential()

# Navigate through multiple stations
move_task_list = [
    {"id": "LM9", "source_id": "LM2", "task_id": "task_001"},
    {"id": "LM5", "source_id": "LM9", "task_id": "task_002"},
    {"id": "LM2", "source_id": "LM5", "task_id": "task_003"}
]

result = robot.task.gotargetlist(move_task_list)

# Monitor task status
while True:
    status = robot.status.query_status('task')
    if status['task_status'] == 4:  # COMPLETED
        print("Task completed!")
        break
    time.sleep(1)

robot.disconnect_all()
```

## Project Structure

```
seer_control/
├── seer_control/              # Main package directory
│   ├── __init__.py           # Package initialization and exports
│   ├── seer_controller.py    # Unified controller (main entry point)
│   ├── seer_controller_base.py    # Base class for all controllers
│   ├── seer_status_controller.py  # Status queries
│   ├── seer_task_controller.py    # Task/motion control
│   ├── seer_control_controller.py # Control operations
│   ├── seer_config_controller.py  # Configuration
│   ├── seer_other_controller.py   # Other operations
│   ├── seer_push_controller.py    # Push data monitoring
│   └── util.py               # Utility functions
├── test_unifiy.py            # Example test script
└── README.md                 # This file
```

## Available Controllers

### SeerController (Unified)
The main entry point that provides access to all specialized controllers:

```python
robot = SeerController('192.168.1.123')
robot.status    # Status controller
robot.task      # Task controller
robot.control   # Control controller
robot.config    # Config controller
robot.other     # Other operations controller
robot.push      # Push data controller
```

### Individual Controllers
You can also use individual controllers directly:

```python
from seer_control import SeerStatusController

status_ctrl = SeerStatusController('192.168.1.123', 19204)
status_ctrl.connect()
position = status_ctrl.query_status('loc')
status_ctrl.disconnect()
```

## Examples

See `test_unifiy.py` for a complete example of:
- Connecting to the robot
- Sending navigation commands
- Monitoring task status
- Handling robot responses

## Development

To run the package modules directly (for testing):

```bash
# Run the unified controller in interactive mode
python -m seer_control.seer_controller

# Run a specific controller
python -m seer_control.seer_status_controller
```

## License

[Add your license information here]

## Author

Assistant
Date: October 21, 2025

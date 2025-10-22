#!/usr/bin/env python3
"""
Flask Web Application for DC Demo 2025 Robot Control

This application provides a web-based interface for controlling the SEER robot
using the DCDemo2025Controller. It offers real-time status updates, trajectory
execution, and manual navigation controls through a user-friendly web interface.

Author: Assistant
Date: October 23, 2025
"""

from flask import Flask, render_template, jsonify, request
import threading
from typing import Optional
import logging
import argparse

from dc_demo_2025_controller import DCDemo2025Controller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dc_demo_2025_secret_key_change_in_production'

# Global robot controller instance
controller: Optional[DCDemo2025Controller] = None
controller_lock = threading.Lock()

# Robot configuration (can be overridden by command line argument)
ROBOT_IP = "192.168.1.123"


# ============================================================================
# Robot Controller Management
# ============================================================================

def initialize_controller():
    """Initialize and connect to the robot controller."""
    global controller
    
    with controller_lock:
        if controller is None:
            logger.info(f"Initializing controller for robot at {ROBOT_IP}")
            controller = DCDemo2025Controller(ROBOT_IP)
            
            if controller.connect(verbose=False):
                logger.info("Controller connected successfully")
                return True
            else:
                logger.error("Failed to connect to robot")
                controller = None
                return False
        return True


def get_controller() -> Optional[DCDemo2025Controller]:
    """Get the robot controller instance."""
    with controller_lock:
        return controller


# ============================================================================
# Flask Routes
# ============================================================================

@app.route('/')
def index():
    """Main control interface page."""
    return render_template('dc_demo_2025.html')


@app.route('/api/status')
def get_status():
    """Get robot connection status."""
    ctrl = get_controller()
    
    if ctrl is None:
        return jsonify({
            'connected': False,
            'robot_ip': ROBOT_IP
        })
    
    return jsonify({
        'connected': ctrl.is_connected,
        'robot_ip': ROBOT_IP
    })


@app.route('/api/connect', methods=['POST'])
def connect_robot():
    """Connect to the robot."""
    try:
        if initialize_controller():
            return jsonify({
                'success': True,
                'message': 'Connected to robot successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect to robot'
            }), 500
    except Exception as e:
        logger.error(f"Error connecting to robot: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/disconnect', methods=['POST'])
def disconnect_robot():
    """Disconnect from the robot."""
    global controller
    
    try:
        with controller_lock:
            if controller:
                controller.disconnect(verbose=False)
                controller = None
        
        return jsonify({
            'success': True,
            'message': 'Disconnected from robot'
        })
    except Exception as e:
        logger.error(f"Error disconnecting from robot: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/trajectories')
def get_trajectories():
    """Get list of available trajectories."""
    ctrl = get_controller()
    
    if ctrl is None:
        return jsonify({
            'success': False,
            'message': 'Controller not initialized'
        }), 400
    
    trajectories = list(ctrl.move_task_list.keys())
    
    return jsonify({
        'success': True,
        'trajectories': trajectories
    })


@app.route('/api/navigate', methods=['POST'])
def navigate():
    """Execute a navigation trajectory."""
    ctrl = get_controller()
    
    if ctrl is None or not ctrl.is_connected:
        return jsonify({
            'success': False,
            'message': 'Robot not connected'
        }), 400
    
    data = request.json
    trajectory = data.get('trajectory')
    wait = data.get('wait', False)  # Default to non-blocking for web interface
    timeout = data.get('timeout', 600.0)
    
    if not trajectory:
        return jsonify({
            'success': False,
            'message': 'Trajectory name is required'
        }), 400
    
    try:
        # Execute navigation in non-blocking mode for web interface
        result = ctrl.navigate(trajectory, wait=wait, timeout=timeout)
        
        return jsonify({
            'success': result.get('success', False),
            'task_id': result.get('task_id'),
            'message': f"Navigation '{trajectory}' started" if result.get('success') else 'Navigation failed'
        })
    except Exception as e:
        logger.error(f"Error executing navigation: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/goto_navigate_start', methods=['POST'])
def goto_navigate_start():
    """Navigate to the starting position of a trajectory."""
    ctrl = get_controller()
    
    if ctrl is None or not ctrl.is_connected:
        return jsonify({
            'success': False,
            'message': 'Robot not connected'
        }), 400
    
    data = request.json
    trajectory = data.get('trajectory')
    wait = data.get('wait', False)
    timeout = data.get('timeout', 60.0)
    
    if not trajectory:
        return jsonify({
            'success': False,
            'message': 'Trajectory name is required'
        }), 400
    
    try:
        result = ctrl.goto_navigate_start(trajectory, wait=wait, timeout=timeout)
        
        return jsonify({
            'success': result.get('success', False),
            'task_id': result.get('task_id'),
            'start_position': result.get('start_position'),
            'message': f"Going to start position: {result.get('start_position')}" if result.get('success') else 'Failed to go to start position'
        })
    except Exception as e:
        logger.error(f"Error going to start position: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/goto', methods=['POST'])
def goto():
    """Navigate to a specific target."""
    ctrl = get_controller()
    
    if ctrl is None or not ctrl.is_connected:
        return jsonify({
            'success': False,
            'message': 'Robot not connected'
        }), 400
    
    data = request.json
    target_id = data.get('target_id')
    wait = data.get('wait', False)
    timeout = data.get('timeout', 60.0)
    
    if not target_id:
        return jsonify({
            'success': False,
            'message': 'Target ID is required'
        }), 400
    
    try:
        result = ctrl.goto(target_id, wait=wait, timeout=timeout)
        
        return jsonify({
            'success': result.get('success', False),
            'task_id': result.get('task_id'),
            'already_at_target': result.get('already_at_target', False),
            'message': f"Navigation to {target_id} started" if result.get('success') else f'Failed to navigate to {target_id}'
        })
    except Exception as e:
        logger.error(f"Error navigating to target: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/task_status')
def get_task_status():
    """Get current task status."""
    ctrl = get_controller()
    
    if ctrl is None or not ctrl.is_connected:
        return jsonify({
            'success': False,
            'message': 'Robot not connected'
        }), 400
    
    try:
        status = ctrl.task_status()
        
        status_map = {
            0: "NONE", 1: "WAITING", 2: "RUNNING", 3: "SUSPENDED",
            4: "COMPLETED", 5: "FAILED", 6: "CANCELED", -1: "ERROR"
        }
        
        return jsonify({
            'success': True,
            'status_code': status,
            'status_text': status_map.get(status, "UNKNOWN")
        })
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/idle_time')
def get_idle_time():
    """Get robot idle time."""
    ctrl = get_controller()
    
    if ctrl is None or not ctrl.is_connected:
        return jsonify({
            'success': False,
            'message': 'Robot not connected'
        }), 400
    
    try:
        idle_time = ctrl.get_idle_time()
        
        return jsonify({
            'success': True,
            'idle_time': idle_time
        })
    except Exception as e:
        logger.error(f"Error getting idle time: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/push_data')
def get_push_data():
    """Get latest push data from robot."""
    ctrl = get_controller()
    
    if ctrl is None or not ctrl.is_connected:
        return jsonify({
            'success': False,
            'message': 'Robot not connected'
        }), 400
    
    try:
        push_data = ctrl.get_push_data()
        
        return jsonify({
            'success': True,
            'data': push_data
        })
    except Exception as e:
        logger.error(f"Error getting push data: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='DC Demo 2025 Web Control Interface')
    parser.add_argument(
        '--robot-ip',
        type=str,
        default=ROBOT_IP,
        help=f'IP address of the robot (default: {ROBOT_IP})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the web server on (default: 5000)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind the web server to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    args = parser.parse_args()
    
    # Set robot IP from command line argument
    ROBOT_IP = args.robot_ip
    
    logger.info("Starting DC Demo 2025 Web Control Interface")
    logger.info(f"Robot IP: {ROBOT_IP}")
    logger.info(f"Server: http://{args.host}:{args.port}")
    
    # Run the Flask app
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

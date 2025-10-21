#!/usr/bin/env python3
"""
SEER Robot Status Controller

This module provides a simple wrapper for querying various robot status information
including robot info, runtime statistics, position, speed, battery, sensors, and much more.

Features:
- Unified status query interface with parameter-based query types
- Support for 65+ status query types
- Automatic request/response ID mapping (response_id = request_id + 10000)
- Per-query-type statistics tracking

Supported query types include:
- Basic: info, run, loc, speed, battery, block
- Sensors: laser, ultrasonic, imu, rfid, pgv
- Hardware: motor, encoder, jack, fork, roller
- Status: task, alarm, emergency, reloc, loadmap
- Map: map, station, mapmd5, get_path
- I/O: io, modbus, canframe
- Advanced: arm_status, arm_move, arm_task
- And many more...

Manual: https://seer-group.feishu.cn/wiki/WsI2wM46YiESh8k12EBclv23nOf?table=tblObW6PmjUPTyTn&view=vewiqqgyEX

Author: Assistant
Date: October 18, 2025
"""

from typing import Optional, Dict, Any, List
try:
    from .seer_controller_base import SeerControllerBase
except ImportError:
    from seer_controller_base import SeerControllerBase

# Status query type definitions
# Format: query_type -> (request_id, response_id, description)
# Response ID = Request ID + 10000
STATUS_QUERY_TYPES = {
    'bins': (1803, 11803, 'Query robot bin information'),
    'info': (1000, 11000, 'Query robot information'),
    'run': (1002, 11002, 'Query robot runtime information'),
    'loc': (1004, 11004, 'Query robot position'),
    'speed': (1005, 11005, 'Query robot speed'),
    'block': (1006, 11006, 'Query robot blocked status'),
    'encoder': (1018, 11018, 'Query encoder pulse value'),
    'battery': (1007, 11007, 'Query robot battery status'),
    'modbus': (1071, 11071, 'Query modbus data'),
    'motor': (1040, 11040, 'Query motor status information'),
    'laser': (1009, 11009, 'Query robot laser point cloud data'),
    'slam': (1025, 11025, 'Query robot SLAM mapping status'),
    'area': (1011, 11011, 'Query robot current area'),
    'emergency': (1012, 11012, 'Query robot emergency stop status'),
    'io': (1013, 11013, 'Query robot I/O data'),
    'imu': (1014, 11014, 'Query robot IMU data'),
    'rfid': (1015, 11015, 'Query RFID data'),
    'ultrasonic': (1016, 11016, 'Query robot ultrasonic sensor data'),
    'pgv': (1017, 11017, 'Query QR code data (PGV)'),
    'task': (1020, 11020, 'Query robot navigation status'),
    'task_status': (1110, 11110, 'Query robot task status package'),
    'reloc': (1021, 11021, 'Query robot localization status'),
    'loadmap': (1022, 11022, 'Query robot map loading status'),
    'jack': (1027, 11027, 'Query jack mechanism status'),
    'fork': (1028, 11028, 'Query fork (forklift) status'),
    'roller': (1029, 11029, 'Query roller (belt) status'),
    'alarm': (1050, 11050, 'Query robot alarm status'),
    'all1': (1100, 11100, 'Query batch data 1'),
    'all2': (1101, 11101, 'Query batch data 2'),
    'all3': (1102, 11102, 'Query batch data 3'),
    'current_lock': (1060, 11060, 'Query current control owner'),
    'map': (1300, 11300, 'Query loaded map and stored maps'),
    'station': (1301, 11301, 'Query station info in current map'),
    'mapmd5': (1302, 11302, 'Query MD5 of specified map list'),
    'get_path': (1303, 11303, 'Query path between any two points'),
    'calib_support': (1509, 11509, 'Query robot calibration support list'),
    'calib_status': (1510, 11510, 'Query robot calibration status'),
    'calib_data': (1511, 11511, 'Query robot calibration file'),
    'params': (1400, 11400, 'Query robot parameters'),
    'model': (1500, 11500, 'Download robot model file'),
    'uploadfile': (1799, 11799, 'Upload robot file'),
    'downloadfile': (1800, 11800, 'Download robot file'),
    'listfile': (1798, 11798, 'Query robot file list'),
    'script_info': (1506, 11506, 'Query robot script list'),
    'script_details': (1507, 11507, 'Query robot script details list'),
    'script_args': (1508, 11508, 'Query robot script default parameters'),
    'transparent': (1900, 11900, 'Query transparent data'),
    'arm_calculate': (1670, 11670, 'Calculate robot arm coordinate transformation'),
    'arm_status': (1669, 11669, 'Query robot arm status'),
    'arm_move': (1673, 11673, 'Robot arm motion control'),
    'arm_task': (1671, 11671, 'Robot arm bin task'),
    'arm_operation': (1674, 11674, 'Robot arm teach panel control'),
    'reco_files': (1676, 11676, 'Simulation recognition from files'),
    'cloud_projection': (1675, 11675, 'Query current recognition camera point cloud image'),
    'battery_script_start': (1901, 11901, 'Run external battery script'),
    'battery_script_stop': (1902, 11902, 'Stop external battery script'),
    'dmx_script_start': (1903, 11903, 'Run ambient light script'),
    'dmx_script_stop': (1904, 11904, 'Stop ambient light script'),
    'canframe': (1750, 11750, 'Query driver parameters'),
    '3dtag': (1665, 11665, 'Query 3D QR code during mapping'),
    'gnss_check': (1760, 11760, 'Query GNSS connection status'),
    'gnss_list': (1761, 11761, 'Query GNSS device list'),
    'sound': (1850, 11850, 'Query currently playing audio name'),
    'joystick_keymap': (1852, 11852, 'Download joystick custom binding events'),
}


class SeerStatusController(SeerControllerBase):
    """
    SEER Robot Status Controller.
    
    Provides a flexible interface for querying various robot status information.
    Uses a unified query method with parameter-based query types.
    
    Supported query types include:
    - 'info': Robot information
    - 'run': Runtime status (uptime, mileage, etc.)
    - 'loc': Robot position
    - 'speed': Robot speed
    - 'battery': Battery status
    - 'laser': Laser point cloud data
    - 'io': I/O data
    - 'alarm': Alarm status
    - And many more (65+ query types supported)
    
    Use get_available_query_types() to see all available query types.
    
    Example:
        controller = SeerStatusController('192.168.192.5')
        controller.connect()
        
        # Query position
        position = controller.query_status('loc')
        print(f"Position: {position['x']}, {position['y']}")
        
        # Query speed
        speed = controller.query_status('speed')
        print(f"Speed: {speed}")
        
        controller.disconnect()
    """
    
    def __init__(self, robot_ip: str = '192.168.192.5', robot_port: int = 19204):
        """
        Initialize the status controller.
        
        Args:
            robot_ip: IP address of the robot (default: 192.168.192.5)
            robot_port: Port number for status queries (default: 19204)
        """
        super().__init__(robot_ip, robot_port)
        
        # Query-specific statistics
        self.query_stats = {query_type: {'count': 0, 'success': 0, 'failed': 0} 
                           for query_type in STATUS_QUERY_TYPES.keys()}
    
    @staticmethod
    def get_available_query_types() -> List[str]:
        """
        Get list of all available query types.
        
        Returns:
            List of query type strings (e.g., ['info', 'run', 'loc', 'speed'])
        """
        return list(STATUS_QUERY_TYPES.keys())
    
    @staticmethod
    def get_query_info(query_type: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific query type.
        
        Args:
            query_type: Query type string (e.g., 'loc', 'speed')
            
        Returns:
            Dictionary with query information:
            - request_id: Request message ID
            - response_id: Response message ID
            - description: Human-readable description
            Returns None if query type not found
        """
        if query_type not in STATUS_QUERY_TYPES:
            return None
        
        req_id, resp_id, desc = STATUS_QUERY_TYPES[query_type]
        return {
            'request_id': req_id,
            'response_id': resp_id,
            'description': desc
        }
    
    def query_status(self, query_type: str, timeout: float = 5.0, **params) -> Optional[Dict[str, Any]]:
        """
        Query robot status for a specific type.
        
        This is the main query method that handles all status queries through
        a unified interface. Query type is specified as a parameter.
        
        Args:
            query_type: Type of status to query ('info', 'run', 'loc', 'speed', etc.)
            timeout: Query timeout in seconds (default: 5.0)
            **params: Optional keyword arguments to pass to the query command
            
        Returns:
            Dictionary containing the query response data if successful, None if failed
            
        Raises:
            ValueError: If query_type is not supported
            
        Example:
            # Query position (no parameters)
            position = controller.query_status('loc')
            if position:
                print(f"x={position['x']}, y={position['y']}")
            
            # Query speed (no parameters)
            speed = controller.query_status('speed')
            if speed:
                print(f"vx={speed['vx']}, vy={speed['vy']}")
            
            # Query with parameters (e.g., get_path between two points)
            path = controller.query_status('get_path',
                map_name='warehouse',
                start_x=0.0,
                start_y=0.0,
                end_x=10.0,
                end_y=5.0
            )
            
            # Query map MD5 for specific maps
            md5 = controller.query_status('mapmd5', 
                map_list=['map1', 'map2', 'map3']
            )
            
            # From command line parsing:
            # "query_status loc" -> query_status('loc')
            # "query_status get_path map_name=warehouse start_x=0.0" 
            #   -> query_status('get_path', map_name='warehouse', start_x=0.0)
        """
        # Validate query type
        if query_type not in STATUS_QUERY_TYPES:
            raise ValueError(f"Unknown query type: '{query_type}'. "
                           f"Available types: {list(STATUS_QUERY_TYPES.keys())}")
        
        # Get request and response IDs for this query type
        request_id, response_id, description = STATUS_QUERY_TYPES[query_type]
        
        # Update statistics
        self.query_stats[query_type]['count'] += 1
        
        # Send query command with params as message payload
        result = self.send_command(
            req_id=1,
            msg_type=request_id,
            msg=params,
            expected_response=response_id,
            timeout=timeout
        )
        
        # Update statistics
        if result is not None:
            self.query_stats[query_type]['success'] += 1
        else:
            self.query_stats[query_type]['failed'] += 1
        
        return result
    
    def get_query_stats(self, query_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get query statistics.
        
        Args:
            query_type: Specific query type to get stats for, or None for all types
            
        Returns:
            Dictionary containing query statistics
        """
        if query_type:
            if query_type not in self.query_stats:
                return {}
            stats = self.query_stats[query_type].copy()
            if stats['count'] > 0:
                stats['success_rate'] = (stats['success'] / stats['count']) * 100
            else:
                stats['success_rate'] = 0.0
            return stats
        else:
            # Return stats for all query types
            all_stats = {}
            for qtype, stats in self.query_stats.items():
                qstats = stats.copy()
                if qstats['count'] > 0:
                    qstats['success_rate'] = (qstats['success'] / qstats['count']) * 100
                else:
                    qstats['success_rate'] = 0.0
                all_stats[qtype] = qstats
            return all_stats


def main():
    """
    Interactive command-line interface for testing status queries.
    
    Allows entering commands like:
        query_status loc
        query_status battery
        query_status get_path map_name=warehouse start_x=0.0 end_x=10.0
        exit
    """
    from util import parse_command_line
    import json
    
    print("🤖 SEER Status Controller - Interactive Mode")
    print("=" * 60)
    
    # Create controller
    controller = SeerStatusController(robot_ip='192.168.1.123', robot_port=19204)
    print(f"Controller: {controller}")
    
    # Show available query types
    query_types = controller.get_available_query_types()
    print(f"\nAvailable query types ({len(query_types)} total):")
    print("Common queries:")
    common_queries = ['info', 'run', 'loc', 'speed', 'battery', 'task', 'task_status', 
                      'alarm', 'io', 'laser', 'imu', 'map', 'station']
    for qtype in common_queries:
        if qtype in query_types:
            info = controller.get_query_info(qtype)
            print(f"  - {qtype:20s} : {info['description']}")
    print(f"\n  ... and {len(query_types) - len(common_queries)} more")
    print("  (Type 'list' to see all available query types)")
    
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
    print("  <query_type> [param1=value1 param2=value2 ...]")
    print("\nExamples:")
    print("  loc")
    print("  battery")
    print("  task_status")
    print("  get_path map_name=warehouse start_x=0.0 end_x=10.0")
    print("  mapmd5 map_list=['map1','map2']")
    print("\nType 'exit' or 'quit' to disconnect and exit.")
    print("Type 'help' or 'list' to show available query types.")
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
            
            # Check for help/list command
            if line.lower() in ['help', 'list']:
                print("\nAll available query types:")
                for i, qtype in enumerate(sorted(query_types), 1):
                    info = controller.get_query_info(qtype)
                    print(f"  {i:2d}. {qtype:20s} : {info['description']}")
                continue
            
            # Parse command line - treat first word as query_type
            parts = line.strip().split()
            if not parts:
                continue
            
            query_type = parts[0]
            
            # Check if query type is valid
            if query_type not in query_types:
                print(f"❌ Unknown query type: {query_type}")
                print("   Type 'list' to see all available query types")
                continue
            
            # Parse parameters from remaining parts
            _, params = parse_command_line(line)
            
            # Get query info
            query_info = controller.get_query_info(query_type)
            
            # Call the function with error handling
            try:
                param_str = ', '.join(f'{k}={v}' for k, v in params.items()) if params else ''
                print(f"⚙️  Querying '{query_type}' ({query_info['description']})")
                if param_str:
                    print(f"   Parameters: {param_str}")
                
                result = controller.query_status(query_type, **params)
                
                if result is not None:
                    # Print full JSON response
                    print("\n📥 Response:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    # Check return code
                    ret_code = result.get('ret_code', -1)
                    if ret_code == 0:
                        print("\n✅ Query succeeded!")
                    else:
                        error_msg = result.get('err_msg', 'Unknown error')
                        print(f"\n❌ Query failed with code {ret_code}: {error_msg}")
                else:
                    print("❌ Query failed - no response received")
                    
            except ValueError as e:
                print(f"❌ Invalid query type: {e}")
            except TypeError as e:
                print(f"❌ Invalid parameters: {e}")
                print(f"   Usage: Check function signature or documentation")
            except Exception as e:
                print(f"❌ Error executing query: {e}")
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

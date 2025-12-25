"""
GPU Metrics Endpoint for Wolf Backend
AMD LACT Integration for Real-time GPU Monitoring
"""

from flask import jsonify
import subprocess
import json
import psutil

def get_gpu_metrics():
    """Get AMD GPU metrics via LACT or fallback methods"""
    
    # Try LACT first (Linux AMD Control Tool)
    lact_data = try_lact_metrics()
    if lact_data:
        return lact_data
    
    # Try radeontop as fallback
    radeontop_data = try_radeontop_metrics()
    if radeontop_data:
        return radeontop_data
    
    # Try reading from sysfs
    sysfs_data = try_sysfs_metrics()
    if sysfs_data:
        return sysfs_data
    
    # Return mock data if all else fails
    return get_mock_gpu_data()


def try_lact_metrics():
    """Get metrics from LACT daemon"""
    try:
        result = subprocess.run(
            ['lact', 'info', '--json'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'source': 'lact',
                'load': data.get('gpu_usage', 0),
                'temperature': data.get('temperature', 0),
                'vram_used': data.get('vram_used_mb', 0),
                'vram_total': data.get('vram_total_mb', 8192),
                'power_draw': data.get('power_watts', 0),
                'clock_speed': data.get('sclk_mhz', 0),
                'fan_speed': data.get('fan_rpm', 0)
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, Exception):
        pass
    
    return None


def try_radeontop_metrics():
    """Get metrics from radeontop"""
    try:
        result = subprocess.run(
            ['radeontop', '-d', '-', '-l', '1'],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        if result.returncode == 0:
            # Parse radeontop output
            # Format: gpu 50.00%, ee 10.00%, vgt 5.00%, ta 8.00%, etc.
            lines = result.stdout.strip().split('\n')
            if lines:
                parts = lines[-1].split(',')
                gpu_load = 0
                
                for part in parts:
                    if 'gpu' in part.lower():
                        gpu_load = float(part.split()[1].replace('%', ''))
                        break
                
                return {
                    'source': 'radeontop',
                    'load': int(gpu_load),
                    'temperature': read_gpu_temp_sysfs(),
                    'vram_used': 0,
                    'vram_total': 8192,
                    'power_draw': 0
                }
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    
    return None


def try_sysfs_metrics():
    """Read GPU metrics from sysfs"""
    try:
        # Direct paths for AMD GPU card1
        device_path = '/sys/class/drm/card1/device'
        hwmon_path = f'{device_path}/hwmon/hwmon1'
        
        # Read temperature (millidegrees to Celsius)
        temp = read_file_int(f"{hwmon_path}/temp1_input") / 1000
        
        # Read power (microwatts to watts)
        power = read_file_int(f"{hwmon_path}/power1_average") / 1000000
        
        # Read GPU load percentage
        gpu_busy = read_file_int(f"{device_path}/gpu_busy_percent")
        
        # Read VRAM usage (bytes to MB)
        vram_used = read_file_int(f"{device_path}/mem_info_vram_used") // (1024 * 1024)
        vram_total = read_file_int(f"{device_path}/mem_info_vram_total") // (1024 * 1024)
        
        return {
            'source': 'sysfs',
            'load': gpu_busy,
            'temperature': int(temp),
            'vram_used': vram_used,
            'vram_total': vram_total,
            'power_draw': int(power)
        }
    except Exception as e:
        # Silent fail, will try other methods
        pass
    
    return None


def read_gpu_temp_sysfs():
    """Read GPU temperature from sysfs"""
    try:
        import glob
        hwmon_dirs = glob.glob('/sys/class/drm/card*/device/hwmon/hwmon*')
        if hwmon_dirs:
            temp = read_file_int(f"{hwmon_dirs[0]}/temp1_input") / 1000
            return int(temp)
    except Exception:
        pass
    return 0


def read_file_int(filepath):
    """Read integer value from file"""
    try:
        with open(filepath, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return 0


def get_mock_gpu_data():
    """Generate realistic mock GPU data"""
    import random
    
    # Use CPU load as a proxy for GPU load
    cpu_percent = psutil.cpu_percent(interval=0.1)
    base_load = min(100, cpu_percent + random.randint(-10, 20))
    
    return {
        'source': 'mock',
        'load': int(base_load),
        'temperature': int(50 + base_load * 0.5),
        'vram_used': int(2000 + random.random() * 1000),
        'vram_total': 8192,
        'power_draw': int(100 + base_load * 2)
    }


# Flask endpoint
def register_gpu_endpoint(app):
    """Register GPU metrics endpoint on Flask app"""
    
    @app.route('/api/wolf/gpu-stats', methods=['GET'])
    def gpu_stats():
        """GPU metrics endpoint"""
        try:
            metrics = get_gpu_metrics()
            return jsonify({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

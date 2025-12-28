import json
import os

RTSP_CONFIG_FILE = "rtsp_config.json"

def load_rtsp_config():
    """Load RTSP configuration from JSON file"""
    if os.path.exists(RTSP_CONFIG_FILE):
        try:
            with open(RTSP_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_rtsp_config(config):
    """Save RTSP configuration to JSON file"""
    with open(RTSP_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_rtsp_config(device_id):
    """Get RTSP configuration for a specific device"""
    config = load_rtsp_config()
    return config.get(device_id, {
        "username": "",
        "password": "",
        "ip_type": "private",  # private, public, or custom
        "custom_ip": ""
    })

def set_rtsp_config(device_id, username, password, ip_type, custom_ip=""):
    """Set RTSP configuration for a specific device"""
    config = load_rtsp_config()
    config[device_id] = {
        "username": username,
        "password": password,
        "ip_type": ip_type,
        "custom_ip": custom_ip
    }
    save_rtsp_config(config)

def cleanup_rtsp_config(valid_device_ids):
    """Remove RTSP configs for devices that are no longer in the device list"""
    config = load_rtsp_config()
    if not config:
        return
    
    # Get list of device IDs to remove
    config_device_ids = set(config.keys())
    valid_device_ids_set = set(valid_device_ids)
    removed_device_ids = config_device_ids - valid_device_ids_set
    
    # Remove configs for devices that no longer exist
    if removed_device_ids:
        for device_id in removed_device_ids:
            del config[device_id]
        save_rtsp_config(config)

def delete_rtsp_config(device_id):
    """Delete RTSP configuration for a specific device"""
    config = load_rtsp_config()
    if device_id in config:
        del config[device_id]
        save_rtsp_config(config)
        return True
    return False

def build_rtsp_url(device_id, device_details, rtsp_config):
    """Build RTSP URL from device details and RTSP config"""
    print(f"Building RTSP URL for device_id: {device_id}")
    print(f"Device details: {device_details}")
    print(f"RTSP config: {rtsp_config}")
    
    if not rtsp_config:
        print("RTSP config is empty")
        return None
    
    username = rtsp_config.get("username", "").strip()
    password = rtsp_config.get("password", "").strip()
    
    if not username or not password:
        print(f"Missing username or password. Username: '{username}', Password: {'*' * len(password) if password else 'empty'}")
        return None
    
    ip_type = rtsp_config.get("ip_type", "private")
    custom_ip = rtsp_config.get("custom_ip", "").strip()
    
    # Determine IP address
    if ip_type == "private":
        ip = device_details.get("private_ip")
        print(f"Using private IP: {ip}")
    elif ip_type == "public":
        ip = device_details.get("public_ip")
        print(f"Using public IP: {ip}")
    else:  # custom
        ip = custom_ip
        print(f"Using custom IP: {ip}")
        # If custom IP is empty, fall back to private IP
        if not ip:
            print("Custom IP is empty, falling back to private IP")
            ip = device_details.get("private_ip")
    
    if not ip:
        print(f"No IP address found for type: {ip_type}")
        return None
    
    # Standard RTSP URL format for Tapo cameras
    # Try different common RTSP paths
    # Most Tapo cameras use /stream1 or /stream2
    rtsp_paths = ["/stream1", "/stream2", "/stream", "/h264"]
    
    # For now, use /stream1 as default (most common for Tapo)
    # You can extend this to try multiple paths if needed
    rtsp_path = "/stream1"
    
    rtsp_url = f"rtsp://{username}:{password}@{ip}:554{rtsp_path}"
    print(f"Built RTSP URL: rtsp://{username}:***@{ip}:554{rtsp_path}")
    return rtsp_url


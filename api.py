import requests
from dotenv import load_dotenv
import os
import warnings
from urllib3.exceptions import InsecureRequestWarning
import sys

warnings.simplefilter('ignore', InsecureRequestWarning)


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Load .env file
dotenv_path = resource_path(".env")
load_dotenv(dotenv_path)

authorization=os.getenv("Authorization")
x_term_id=os.getenv("X-Term-Id")


default_url = "https://aps1-app-server.iot.i.tplinkcloud.com/v1/things/{device_id}/services-sync"
initial_information_url = "https://aps1-app-server.iot.i.tplinkcloud.com/v1/families/default/thing-order"
EDGE_BASE_URL = "https://ain1-edge-server.iot.i.tplinkcloud.com/v1/things/{device_id}/services-sync"


headers = {
    "Authorization": authorization,
    "App-Cid": f"app:TP-Link_Tapo_Android:{x_term_id}",
    "X-App-Name": "TP-Link_Tapo_Android",
    "X-App-Version": "3.15.117",
    "X-Term-Id": f"{x_term_id}",
    "X-Ospf": "Android 11",
    "X-Net-Type": "wifi",
    "X-Strict": "0",
    "X-Locale": "en_US",
    "User-Agent": "TP-Link_Tapo_Android/3.15.117",
    "Content-Type": "application/json; charset=UTF-8"
}

def get_headers():
    """Get headers with current credentials (reloads from env)"""
    load_dotenv(override=True)
    authorization = os.getenv("Authorization")
    x_term_id = os.getenv("X-Term-Id")
    
    if not authorization or not x_term_id:
        return None
    
    return {
        "Authorization": authorization,
        "App-Cid": f"app:TP-Link_Tapo_Android:{x_term_id}",
        "X-App-Name": "TP-Link_Tapo_Android",
        "X-App-Version": "3.15.117",
        "X-Term-Id": f"{x_term_id}",
        "X-Ospf": "Android 11",
        "X-Net-Type": "wifi",
        "X-Strict": "0",
        "X-Locale": "en_US",
        "User-Agent": "TP-Link_Tapo_Android/3.15.117",
        "Content-Type": "application/json; charset=UTF-8"
    }

def get_all_devices():
    headers = get_headers()
    if not headers:
        print("Error: Authorization and X-Term-Id must be configured")
        return False
    
    params = {
        "page": 0,
        "pageSize": 20
    }

    response = requests.get(initial_information_url, headers=headers, params=params, timeout=10, verify=False)
    
    if response.status_code != 200:
        print(f"Error, Status Code: {response.status_code}, Content Body: {response.content}")
        return False
    
    try:
        data = response.json()

        # print("Raw output\n\n", data, "\n\n")
        print(f"API Response data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        
        if 'data' not in data:
            print(f"Response structure: {data}")
            return False
        
        all_devices = []
        for entry in data['data']:
            if 'thingOrders' in entry:
                for item in entry['thingOrders']:
                    device_id = item.replace("Device-", "")
                    if device_id not in all_devices:
                        all_devices.append(device_id)
        
        print(f"Extracted {len(all_devices)} device IDs: {all_devices}")
        return all_devices
    except Exception as e:
        print(f"Error parsing response: {e}")
        import traceback
        traceback.print_exc()
        return False
        
def get_device_details(device_id):
    if not device_id:
        print("Please provide a device id")
        return False
    
    headers = get_headers()
    if not headers:
        print("Error: Authorization and X-Term-Id must be configured")
        return False
    
    url = default_url.replace("{device_id}", device_id)

    payload = {
        "inputParams": {
            "requestData": {
                "method": "multipleRequest",
                "params": {
                    "requests": [
                        {
                            "method": "getDeviceInfo",
                            "params": {
                                "device_info": {
                                    "name": ["basic_info"]
                                }
                            }
                        },
                        {
                            "method": "getUpnpStatus",
                            "params": {
                                "upnpc": {
                                    "table": ["upnp_status"]
                                }
                            }
                        },
                        {
                            "method": "getPubIP",
                            "params": {
                                "upnpc": {
                                    "name": ["pub_ip"]
                                }
                            }
                        }
                    ]
                }
            }
        },
        "serviceId": "passthrough"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
        verify=False
    )

    if response.status_code != 200:
        print(f"[!] Failed for {device_id}: {response.status_code}")
        return None

    resp = response.json()
    responses = resp["outputParams"]["responseData"]["result"]["responses"]

    result = {
        "name": None,
        "device_name": None,
        "longitude": None,
        "latitude": None,
        "private_ip": None,
        "public_ip": None
    }

    for r in responses:
        method = r["method"]

        if method == "getDeviceInfo":
            info = r["result"]["device_info"]["basic_info"]
            result["name"] = info.get("device_alias")
            result["device_name"] = info.get("device_name")
            result["longitude"] = info.get("longitude")
            result["latitude"] = info.get("latitude")

        elif method == "getUpnpStatus":
            upnp = r["result"]["upnpc"]["upnp_status"]
            if upnp and "vhttpd" in upnp[0]:
                result["private_ip"] = upnp[0]["vhttpd"].get("ipaddr")

        elif method == "getPubIP":
            result["public_ip"] = r["result"]["upnpc"]["pub_ip"].get("ip")

    return result

def get_presets(device_id):
    if not device_id:
        print("Please provide a device id")
        return None
    
    headers = get_headers()
    if not headers:
        print("Error: Authorization and X-Term-Id must be configured")
        return None

    url = default_url.replace("{device_id}", device_id)

    payload = {
        "inputParams": {
            "requestData": {
                "method": "multipleRequest",
                "params": {
                    "requests": [
                        {
                            "method": "getPresetConfig",
                            "params": {
                                "preset": {
                                    "name": ["preset"]
                                }
                            }
                        }
                    ]
                }
            }
        },
        "serviceId": "passthrough"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
        verify=False
    )

    if response.status_code != 200:
        print(f"[!] Failed for {device_id}: {response.status_code}")
        return None

    resp = response.json()
    responses = resp["outputParams"]["responseData"]["result"]["responses"]

    presets = {}

    for r in responses:
        if r["method"] == "getPresetConfig":
            preset_data = r["result"]["preset"]["preset"]
            ids = preset_data.get("id", [])
            names = preset_data.get("name", [])

            presets = dict(zip(ids, names))

    return presets

def move_to_preset(device_id, preset_id):
    if not device_id or not preset_id:
        print("device_id and preset_id are required")
        return None
    
    headers = get_headers()
    if not headers:
        print("Error: Authorization and X-Term-Id must be configured")
        return None

    url = default_url.replace("{device_id}", device_id)

    payload = {
        "inputParams": {
            "requestData": {
                "method": "multipleRequest",
                "params": {
                    "requests": [
                        {
                            "method": "motorMoveToPreset",
                            "params": {
                                "preset": {
                                    "goto_preset": {
                                        "id": str(preset_id)
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        },
        "serviceId": "passthrough"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
        verify=False
    )

    if response.status_code != 200:
        print(f"[!] HTTP Error: {response.status_code}")
        return None

    resp = response.json()
    
    # Grab the motorMoveToPreset method response
    try:
        method_resp = resp["outputParams"]["responseData"]["result"]["responses"][0]
        error_code = method_resp.get("error_code", -1)
        
        if error_code != 0:
            print(f"[!] Preset {preset_id} is invalid or cannot be used. Error code: {error_code}")
            return None
        else:
            print(f"[+] Preset {preset_id} applied successfully.")
            return method_resp
    except Exception as e:
        print(f"[!] Unexpected response format: {e}")
        return None
    
def move_camera(device_id, axis, value):
    if not device_id:
        print("device_id is required")
        return None

    if axis not in ("x", "y"):
        print("axis must be 'x' or 'y'")
        return None

    if not isinstance(value, int):
        print("value must be an integer (e.g. 10 or -10)")
        return None
    
    headers = get_headers()
    if not headers:
        print("Error: Authorization and X-Term-Id must be configured")
        return None

    url = default_url.replace("{device_id}", device_id)

    # Build motor move params
    move_params = {"x_coord": "0", "y_coord": "0"}
    if axis == "x":
        move_params["x_coord"] = str(value)
    else:
        move_params["y_coord"] = str(value)

    payload = {
        "inputParams": {
            "requestData": {
                "method": "multipleRequest",
                "params": {
                    "requests": [
                        {
                            "method": "motorMove",
                            "params": {
                                "motor": {"move": move_params}
                            }
                        }
                    ]
                }
            }
        },
        "serviceId": "passthrough"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
        verify=False
    )

    if response.status_code != 200:
        print(f"[!] HTTP Error: {response.status_code}")
        return None

    resp = response.json()

    try:
        method_resp = resp["outputParams"]["responseData"]["result"]["responses"][0]
        error_code = method_resp.get("error_code", -1)

        if error_code == 0:
            print(f"[+] Camera moved on {axis}-axis by {value}")
            return method_resp
        elif error_code == -64304:
            print(f"[!] Motor move failed: Camera cannot move further in this direction (error {error_code})")
            return None
        else:
            print(f"[!] Motor move failed. Error code: {error_code}")
            return None

    except Exception as e:
        print(f"[!] Unexpected response format: {e}")
        return None
    

def toggle_privacy_mode(device_id, enabled=True):
    """
    Toggle privacy mode (lens mask) on/off for a Tapo camera
    :param device_id: str - device ID
    :param enabled: bool - True = privacy ON (lens covered), False = privacy OFF
    :return: response or None
    """
    if not device_id:
        print("device_id is required")
        return None

    headers = get_headers()
    if not headers:
        print("Error: Authorization and X-Term-Id must be configured")
        return None

    url = default_url.replace("{device_id}", device_id)
    enabled_value = "on" if enabled else "off"

    payload = {
        "inputParams": {
            "requestData": {
                "method": "multipleRequest",
                "params": {
                    "requests": [{
                        "method": "setLensMaskConfig",
                        "params": {
                            "lens_mask": {
                                "lens_mask_info": {
                                    "enabled": enabled_value
                                }
                            }
                        }
                    }]
                }
            }
        },
        "serviceId": "passthrough"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10, verify=False)
        if response.status_code == 200:
            resp = response.json()
            error_code = resp.get("outputParams", {}) \
                             .get("responseData", {}) \
                             .get("result", {}) \
                             .get("responses", [{}])[0] \
                             .get("error_code", -1)
            if error_code == 0:
                print(f"[+] Privacy mode {'enabled' if enabled else 'disabled'} successfully.")
                return True
            else:
                print(f"[!] Failed to toggle privacy mode. Error code: {error_code}")
                return False
        else:
            print(f"[!] HTTP Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[!] Exception during privacy toggle: {e}")
        return False

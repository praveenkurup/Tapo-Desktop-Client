import json
import os
import time
import requests
from dotenv import load_dotenv

JWT_FILE = "device_jwts.json"

load_dotenv()
APS_TOKEN = os.getenv("Authorization")
X_TERM_ID = os.getenv("X-Term-Id")
APP_CID = f"app:TP-Link_Tapo_Android:{X_TERM_ID}"


def load_jwt_file():
    if not os.path.exists(JWT_FILE):
        return {}
    with open(JWT_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_jwt_file(data):
    with open(JWT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_jwt_from_server():
    """
    Calls /v2/auth/app to get a new JWT for this device
    """
    url = "https://aps1-security.iot.i.tplinknbu.com/v2/auth/app"
    headers = {
        "App-Cid": APP_CID,
        "X-App-Name": "TP-Link_Tapo_Android",
        "X-App-Version": "3.15.117",
        "X-Term-Id": X_TERM_ID,
        "X-Ospf": "Android 11",
        "X-Net-Type": "wifi",
        "X-Strict": "0",
        "X-Locale": "en_US",
        "User-Agent": "TP-Link_Tapo_Android/3.15.117",
        "Content-Type": "application/json; charset=UTF-8",
    }

    payload = {
        "appType": "TP-Link_Tapo_Android",
        "terminalUUID": X_TERM_ID,
        "token": APS_TOKEN
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        data = response.json()
        jwt = data.get("jwt")
        expires_in = data.get("jwtExpiresIn", 0)
        if jwt:
            return jwt, int(time.time()) + expires_in
    except Exception as e:
        print(f"[!] Failed to fetch JWT: {e}")
    
    return None, None


def get_valid_jwt(device_id):
    """
    Returns a valid JWT for the given device_id.
    Automatically fetches a new one if missing or expired.
    """
    jwts = load_jwt_file()
    entry = jwts.get(device_id)

    # check if JWT exists and is still valid
    if entry:
        if time.time() < entry.get("expires_at", 0) - 10:
            return entry["jwt"]

    # missing or expired → fetch new JWT
    jwt, expires_at = fetch_jwt_from_server(device_id)
    if jwt:
        jwts[device_id] = {"jwt": jwt, "expires_at": expires_at}
        save_jwt_file(jwts)
        return jwt

    return None

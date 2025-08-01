import hashlib
import uuid
import time
import requests

# -------------------------------
# 🎯 One-Time QR Token Generator
# -------------------------------

def generate_one_time_token(emp_id: str) -> str:
    """
    Generates a unique token using UUID and timestamp.
    """
    raw = f"{emp_id}-{uuid.uuid4()}-{int(time.time())}"
    return hashlib.sha256(raw.encode()).hexdigest()

def validate_token(token: str, valid_tokens: dict) -> bool:
    """
    Validates and consumes the token. Tokens should be stored temporarily.
    """
    if token in valid_tokens:
        del valid_tokens[token]  # Consume it (one-time use)
        return True
    return False

# -------------------------------
# 🌍 Geo-tagging & IP Tracking
# -------------------------------

def get_public_ip():
    try:
        response = requests.get("https://api64.ipify.org?format=json", timeout=3)
        return response.json().get("ip", "Unknown")
    except:
        return "Unavailable"

def get_geo_location(ip: str):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        data = response.json()
        return {
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_name"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude")
        }
    except:
        return {"error": "Location unavailable"}

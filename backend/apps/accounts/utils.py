import hashlib
import secrets


def generate_email_verification_token():
    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    return raw_token, token_hash

def generate_password_verification_token():
    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    return raw_token, token_hash

def get_device_name(user_agent):
    if not user_agent:
        return "Unknown device"

    user_agent = user_agent.lower()

    # Operating system
    if "windows" in user_agent:
        os_name = "Windows"
    elif "iphone" in user_agent:
        os_name = "iPhone"
    elif "ipad" in user_agent:
        os_name = "iPad"
    elif "android" in user_agent:
        os_name = "Android"
    elif "mac os" in user_agent:
        os_name = "macOS"
    elif "linux" in user_agent:
        os_name = "Linux"
    else:
        os_name = "Unknown OS"

    # Browser
    if "edg/" in user_agent:
        browser = "Edge"
    elif "chrome/" in user_agent:
        browser = "Chrome"
    elif "firefox/" in user_agent:
        browser = "Firefox"
    elif "safari/" in user_agent:
        browser = "Safari"
    else:
        browser = "Unknown browser"

    return f"{browser} on {os_name}"
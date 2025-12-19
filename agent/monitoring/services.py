"""
Business logic services for monitoring app.
"""
import subprocess
import platform
import requests
from django.conf import settings
from django.utils import timezone


def ping_device(ip_address, timeout=4):
    """
    Ping a device using ARP and return success/failure.

    Args:
        ip_address: IP address to ping
        timeout: Timeout in seconds

    Returns:
        bool: True if device responded, False otherwise
    """
    interface = settings.NETWORK_INTERFACE
    command = ['arping', '-c', '4', '-I',
               interface, '-w', str(timeout), ip_address]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 2,
            text=True
        )
        if result.returncode != 0:
            return (False, None)
        import re
        mac_match = re.search(r'from ([0-9a-fA-F:]{17})', result.stdout)
        if mac_match:
            detected_mac = get_normal_mac(mac_match.group(1))
            if detected_mac:
                return (True, detected_mac)
        return (True, None)

    except subprocess.TimeoutExpired:
        return (False, None)
    except Exception as e:
        print(f"Error pinging {ip_address}: {e}")
        return (False, None)


def send_heartbeat(devices_online):
    """
    Send heartbeat to cloud API.

    Args:
        devices_online: List of dicts with employee info currently online

    Returns:
        bool: True if successful, False otherwise
    """
    payload = {
        'siteId': settings.SITE_ID,
        'timestamp': timezone.now().isoformat(),
        'devicesOnline': devices_online
    }

    headers = {
        'Authorization': f'Bearer {settings.AGENT_AUTH_TOKEN}'
    }

    try:
        response = requests.post(
            f"{settings.CLOUD_API_URL}/api/heartbeat",
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        print(
            f"Heartbeat sent successfully with {len(devices_online)} devices")
        return True
    except requests.RequestException as e:
        print(f"Error sending heartbeat: {e}")
        return False


def send_hourly_summary(summaries, downtime_data=None):
    """
    Send hourly summary to cloud API.

    Args:
        summaries: List of dicts with hourly presence data
        downtime_data: Optional list of dicts with agent downtime info

    Returns:
        bool: True if successful, False otherwise
    """
    payload = {
        'siteId': settings.SITE_ID,
        'timestamp': timezone.now().isoformat(),
        'presenceData': summaries
    }

    headers = {
        'Authorization': f'Bearer {settings.AGENT_AUTH_TOKEN}'
    }

    if downtime_data:
        payload['agentDowntimes'] = downtime_data

    try:
        response = requests.post(
            f"{settings.CLOUD_API_URL}/api/presence",
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        print(f"Hourly summary sent successfully: {len(summaries)} records")
        return True
    except requests.RequestException as e:
        print(f"Error sending hourly summary: {e}")
        return False


def get_normal_mac(mac):
    """
    Convert MAC adress with "-" to standard format
    Input formats supported:
        d0:ba:e4:ef:4d:c4
        D0-BA-E4-EF-4D-C4
    Returns: d0:ba:e4:ef:4d:c4 (lowercase, colon-separated)
    """
    if not mac:
        return None

    mac_str = str(mac)
    mac_converted = mac_str.replace('-', ':').lower()
    if len(mac_converted) != 17:
        return None

    return mac_converted

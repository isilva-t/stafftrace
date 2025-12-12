"""
Business logic services for monitoring app.
"""
import subprocess
import platform
import requests
from django.conf import settings
from django.utils import timezone


def ping_device(ip_address, timeout=1):
    """
    Ping a device and return success/failure.

    Args:
        ip_address: IP address to ping
        timeout: Timeout in seconds

    Returns:
        bool: True if ping successful, False otherwise
    """
    command = ['ping', '-c', '1', '-W', str(timeout), ip_address]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 1
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        print(f"Error pinging {ip_address}: {e}")
        return False


def send_heartbeat(devices_online):
    """
    Send heartbeat to cloud API.

    Args:
        devices_online: List of dicts with employee info currently online

    Returns:
        bool: True if successful, False otherwise
    """
    payload = {
        'site_id': settings.SITE_ID,
        'timestamp': timezone.now().isoformat(),
        'devicesOnline': devices_online
    }

    try:
        response = requests.post(
            f"{settings.CLOUD_API_URL}/api/heartbeat",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        print(f"Heartbeat sent successfully:", end=" ")
        print(f"{len(devices_online)} devices online")
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
        'site_id': settings.SITE_ID,
        'timestamp': timezone.now().isoformat(),
        'presenceData': summaries
    }

    if downtime_data:
        payload['agentDowntimes'] = downtime_data

    try:
        response = requests.post(
            f"{settings.CLOUD_API_URL}/api/presence",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        print(f"Hourly summary sent successfully: {len(summaries)} records")
        return True
    except requests.RequestException as e:
        print(f"Error sending hourly summary: {e}")
        return False

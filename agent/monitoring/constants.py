"""
Configuration constants for the monitoring app.
"""
import os

# Ping configuration
PING_INTERVAL_SECONDS = 4              # Ping devices frequency
OFFLINE_THRESHOLD_SECONDS = 15          # Mark offline after X seconds

PING_LOCK_TIMEOUT_SECONDS = int(os.getenv('PING_LOCK_TIMEOUT_SECONDS', 60))

# Cloud communication
HEARTBEAT_INTERVAL_MINUTES = 5          # Send "who's online" every 5 minutes
SUMMARY_INTERVAL_HOURS = 1              # Send hourly summary every hour

# System health
# Consider app crashed if no update in X seconds
SYSTEM_HEARTBEAT_CHECK_SECONDS = 20

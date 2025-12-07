"""
Configuration constants for the monitoring app.
"""

# Ping configuration
PING_INTERVAL_SECONDS = 60              # Ping devices every 1 minute
OFFLINE_THRESHOLD_SECONDS = 60          # Mark offline after 1 min of failed pings

# Cloud communication
HEARTBEAT_INTERVAL_MINUTES = 5          # Send "who's online" every 5 minutes
SUMMARY_INTERVAL_HOURS = 1              # Send hourly summary every hour

# System health
SYSTEM_HEARTBEAT_CHECK_SECONDS = 120    # Consider app crashed if no update in 2 min

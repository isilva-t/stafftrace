"""
Celery periodic tasks for monitoring app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Device, StateChange, User, HourlySummary, SystemStatus
from .services import ping_device, send_heartbeat, send_hourly_summary
from .constants import OFFLINE_THRESHOLD_SECONDS

# In-memory tracker for failed pings
device_failure_tracker = {}


@shared_task
def ping_all_devices():
    """Ping all active devices and update state changes."""
    for device in Device.objects.select_related('user').all():
        ping_success = ping_device(device.ip_address)

        # Get last state change for this device
        last_change = device.state_changes.first()

        if ping_success:
            # Clear failure tracker
            device_failure_tracker.pop(device.id, None)

            # Check if device was offline
            if not last_change or last_change.status == 0:
                # Device came online
                StateChange.objects.create(
                    device=device,
                    user=device.user,
                    timestamp=timezone.now(),
                    status=1  # went online
                )
                print(f"{device.user.employee_name} came ONLINE")
        else:
            # Ping failed
            if device.id not in device_failure_tracker:
                # First failure - start tracking
                device_failure_tracker[device.id] = timezone.now()
            else:
                # Check if threshold reached
                time_failing = (
                    timezone.now() - device_failure_tracker[device.id]).total_seconds()

                if time_failing >= OFFLINE_THRESHOLD_SECONDS:
                    # Mark offline (only if was online)
                    if last_change and last_change.status == 1:
                        StateChange.objects.create(
                            device=device,
                            user=device.user,
                            timestamp=timezone.now(),
                            status=0  # went offline
                        )
                        print(f"{device.user.employee_name} went OFFLINE")
                    # Clear tracker
                    device_failure_tracker.pop(device.id, None)


@shared_task
def send_heartbeat_to_cloud():
    """Send current online status to cloud."""
    devices_online = []

    for user in User.objects.all():
        if user.is_online():
            devices_online.append({
                'employeeId': user.id,
                'employeeName': user.employee_name,
                'fakeName': user.fake_name,
                'area': 'default'  # Hardcoded for MVP
            })

    send_heartbeat(devices_online)


@shared_task
def send_hourly_summary_to_cloud():
    """Calculate hourly summary and send to cloud."""
    # Calculate for the previous complete hour
    end_time = timezone.now().replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=1)

    summaries = []

    for user in User.objects.all():
        # Get state changes in this hour
        changes = user.state_changes.filter(
            timestamp__gte=start_time,
            timestamp__lt=end_time
        ).order_by('timestamp')

        # Get initial state (before hour started)
        initial_state = user.state_changes.filter(
            timestamp__lt=start_time
        ).first()

        # Calculate metrics
        first_seen = None
        last_seen = None
        minutes_online = 0

        currently_online = initial_state and initial_state.status == 1
        online_start = start_time if currently_online else None

        if not changes.exists() and currently_online:
            # Was online entire hour
            first_seen = start_time
            last_seen = end_time
            minutes_online = 60
        else:
            for change in changes:
                if change.status == 1:  # Went online
                    online_start = change.timestamp
                    if first_seen is None:
                        first_seen = change.timestamp
                elif change.status == 0:  # Went offline
                    if online_start:
                        minutes_online += (change.timestamp -
                                           online_start).total_seconds() / 60
                        last_seen = change.timestamp
                        online_start = None

            # If still online at end of hour
            if online_start:
                minutes_online += (end_time -
                                   online_start).total_seconds() / 60
                last_seen = end_time

        # Only send if there was activity
        if first_seen:
            # Save locally
            HourlySummary.objects.create(
                user=user,
                hour=start_time,
                first_seen=first_seen,
                last_seen=last_seen,
                minutes_online=int(minutes_online)
            )

            # Prepare for cloud
            summaries.append({
                'employee_id': user.id,
                'employee_name': user.employee_name,
                'fake_name': user.fake_name,
                'date': start_time.date().isoformat(),
                'hour': start_time.hour,
                'first_seen': first_seen.isoformat(),
                'last_seen': last_seen.isoformat(),
                'minutes_online': int(minutes_online)
            })

    if summaries:
        send_hourly_summary(summaries)


@shared_task
def update_system_heartbeat():
    """Update system heartbeat to track app health."""
    system = SystemStatus.get_instance()
    system.save()  # This updates updated_at automatically

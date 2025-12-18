"""
Celery periodic tasks for monitoring app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Device, StateChange, User, HourlySummary, SystemStatus, AgentDowntime
from .services import ping_device, send_heartbeat, send_hourly_summary
from .constants import OFFLINE_THRESHOLD_SECONDS, PING_LOCK_TIMEOUT_SECONDS, OFFLINE_FAILURE_COUNT
from django.core.cache import cache
from django.db.models import Prefetch
import time

# In-memory tracker for failed pings to user devices
user_failure_tracker = {}


def save_status(device, new_status):
    StateChange.objects.create(
        device=device,
        user=device.user,
        timestamp=timezone.now(),
        status=new_status
    )
    if new_status == 1:
        print(f"{device.user.fake_name} came ONLINE 🟢")
    else:
        print(f"{device.user.fake_name} went OFFLINE 🔴")


@shared_task
def ping_all_devices():
    """Ping all active devices and update state changes.
    Uses Redis lock to prevent overlapping scans."""

    LOCK_KEY = "ping_all_devices_lock"
    LOCK_TIMEOUT = PING_LOCK_TIMEOUT_SECONDS

    lock_acquired = cache.add(LOCK_KEY, "locked", timeout=LOCK_TIMEOUT)

    if not lock_acquired:
        # print("⏭️  Skipping ping scan - previous scan still running")
        return

    start_time = time.time()
    # print("🔒 Lock acquired - starting device scan")
    try:
        changes = 0

        users = User.objects.prefetch_related(
            Prefetch(
                'state_changes',
                queryset=StateChange.objects.all()[:1],
                to_attr='latest_state'
            )
        ).all()

        for user in users:
            any_device_online = False
            online_device = None

            for device in user.devices.all():
                is_online, detected_mac = ping_device(device.ip_address)

                if is_online:
                    any_device_online = True
                    online_device = device
                    break

            last_change = user.state_changes[0] if user.state_changes else None

            if any_device_online:
                user_failure_tracker.pop(user.id, None)

                if not last_change or last_change.status == 0:
                    save_status(device, 1)
                    changes += 1

            else:  # arp failed
                if last_change and last_change.status == 1:
                    print(f"All devices failed for {user.fake_name}. 🟡")
                if user.id not in user_failure_tracker:
                    user_failure_tracker[user.id] = 1
                else:
                    user_failure_tracker[user.id] += 1

                    if user_failure_tracker[user.id] >= OFFLINE_FAILURE_COUNT:
                        if last_change and last_change.status == 1:
                            save_status(device, 0)
                            changes += 1
                        user_failure_tracker.pop(user.id, None)

        if changes > 0:
            send_heartbeat_to_cloud()
        duration = time.time() - start_time
        print(
            f"✅ Scan complete - {changes} changes detected in {duration:.2f}s")
    finally:
        cache.delete(LOCK_KEY)
        # print("🏁 Lock released")


@shared_task
def send_heartbeat_to_cloud():
    """Send current online status to cloud."""
    all_employees = []

    for user in User.objects.all():
        last_state = user.state_changes.first()

        all_employees.append({
            'employeeId': user.id,
            'employeeName': user.fake_name,
            'fakeName': user.fake_name,
            'area': 'default',  # Hardcoded for MVP
            'isPresent': user.is_online(),
            'lastSeen': last_state.timestamp.isoformat() if last_state else None
        })

    if send_heartbeat(all_employees):
        online_count = sum(1 for emp in all_employees if emp['isPresent'])
        print(f"💓 Heartbeat: {online_count}/{len(all_employees)} online")


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
            summary_obj, created = HourlySummary.objects.update_or_create(
                user=user,
                hour=start_time,
                defaults={
                    'first_seen': first_seen,
                    'last_seen': last_seen,
                    'minutes_online': int(minutes_online),
                    'synced': False
                }
            )

            # Prepare for cloud
            payload = {
                'employeeId': user.id,
                'employeeName': user.fake_name,
                'fakeName': user.fake_name,
                'date': start_time.date().isoformat(),
                'hour': start_time.hour,
                'firstSeen': first_seen.time().isoformat(),
                'lastSeen': last_seen.time().isoformat(),
                'minutesOnline': int(minutes_online)
            }

            summaries.append((payload, summary_obj))

    if summaries:

        unsynced_downtimes = AgentDowntime.objects.filter(synced=False)
        downtime_data = None

        if unsynced_downtimes.exists():
            downtime_data = [{
                'downtimeStart': dt.downtime_start.isoformat(),
                'downtimeEnd': dt.downtime_end.isoformat()
            } for dt in unsynced_downtimes]

        for payload, summary_obj in summaries:
            success = send_hourly_summary(
                [payload], downtime_data if downtime_data else None)
            if success:
                summary_obj.synced = True
                summary_obj.save()

                if downtime_data:
                    unsynced_downtimes.update(synced=True)
                    downtime_data = None


@shared_task
def retry_unsynced_summaries():
    """Retry sending unsynced hourly summaries to cloud (newest first)."""

    unsynced = HourlySummary.objects.filter(synced=False).order_by('-hour')

    if not unsynced.exists():
        print("no unsyncend summaries to retry")
        return

    print(f"retrying {unsynced.count()} unsynced summaries...")

    for summary in unsynced:
        payload = {
            'employeeId': summary.user.id,
            'employeeName': summary.user.fake_name,
            'fakeName': summary.user.fake_name,
            'date': summary.hour.date().isoformat(),
            'hour': summary.hour.hour,
            'firstSeen': summary.first_seen.time().isoformat(),
            'lastSeen': summary.last_seen.time().isoformat(),
            'minutesOnline': summary.minutes_online
        }

        success = send_hourly_summary([payload])
        if success:
            summary.synced = True
            summary.save()
            print(f"✓ Synced summary for", end=" ")
            print(f"{summary.user.fake_name} at {summary.hour}")
        else:
            print(f"✗ Failed to sync summary for", end=" ")
            print(f"{summary.user.fake_name} at {summary.hour}")


@shared_task
def update_system_heartbeat():
    """Update system heartbeat to track app health."""
    system = SystemStatus.get_instance()
    system.save()  # This updates updated_at automatically

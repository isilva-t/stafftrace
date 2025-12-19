"""
Celery periodic tasks for monitoring app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Device, StateChange, User, HourlySummary, SystemStatus, AgentDowntime
from .services import send_heartbeat, send_hourly_summary
from .constants import PING_LOCK_TIMEOUT_SECONDS, OFFLINE_FAILURE_COUNT
from django.core.cache import cache
from django.db.models import Prefetch
from .services import get_normal_mac
from config.settings import NETWORK_INTERFACE, SUBNET
import time
import subprocess

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


def get_mac_devices() -> set[str]:
    mac_list = Device.objects.filter(
        mac_address__isnull=False
    ).exclude(
        mac_address=''
    ).values_list('mac_address', flat=True)

    for m in mac_list:
        m = get_normal_mac(m)

    return set(mac_list)


def get_online_devices(mac_devices) -> set[str]:
    command = [
        'arp-scan',
        '--interface', NETWORK_INTERFACE,
        '--retry', '4',
        '--timeout', '500',
        SUBNET
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            text=True,
            check=True
        )
        mac_adresses = set()

        for line in result.stdout.split('\n'):
            parts = line.lower().split()
            for p in parts:
                if p.count(':') == 5 and p in mac_devices:
                    mac_adresses.add(p)

        return mac_adresses

    except subprocess.TimeoutExpired:
        return set()
    except subprocess.CalledProcessError as e:
        return set()
    except Exception as e:
        return set()


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
        mac_devices = get_mac_devices()
        online_devices = get_online_devices(mac_devices)

        for user in users:
            any_device_online = False
            online_device = None

            for device in user.devices.all():
                is_online = device.mac_address in online_devices

                if is_online:
                    any_device_online = True
                    online_device = device
                    break

            last_change = user.latest_state[0] if user.latest_state else None

            if any_device_online:
                user_failure_tracker.pop(user.id, None)

                if not last_change or last_change.status == 0:
                    save_status(device, 1)
                    changes += 1

            else:
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
    """Calculate hourly presence span and send to cloud"""
    end_time = timezone.now().replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=1)

    summaries = []

    for user in User.objects.all():
        changes = user.state_changes.filter(
            timestamp__gte=start_time,
            timestamp__lt=end_time
        ).order_by('timestamp')

        initial_state = user.state_changes.filter(
            timestamp__lt=start_time
        ).order_by('-timestamp').first()

        was_online_at_start = initial_state and initial_state.status == 1

        if not changes.exists():
            if was_online_at_start:
                first_seen = start_time
                last_seen = end_time
            else:
                continue
        else:
            first_change = changes.first()
            last_change = changes.last()
            first_seen = start_time if was_online_at_start else first_change.timestamp
            last_seen = end_time if last_change.status == 1 else last_change.timestamp

        minutes_present = (last_seen - first_seen).total_seconds() / 60

        summary_obj, created = HourlySummary.objects.update_or_create(
            user=user,
            hour=start_time,
            defaults={
                'first_seen': first_seen,
                'last_seen': last_seen,
                'minutes_online': int(minutes_present),
                'synced': False
            }
        )

        payload = {
            'employeeId': user.id,
            'employeeName': user.fake_name,
            'fakeName': user.fake_name,
            'date': start_time.date().isoformat(),
            'hour': start_time.hour,
            'firstSeen': first_seen.time().isoformat(),
            'lastSeen': last_seen.time().isoformat(),
            'minutesOnline': int(minutes_present)
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

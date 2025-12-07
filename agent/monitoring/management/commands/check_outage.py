"""
Management command to check for power outage and mark devices offline if needed.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from monitoring.models import SystemStatus, StateChange, Device
from monitoring.constants import SYSTEM_HEARTBEAT_CHECK_SECONDS, OFFLINE_THRESHOLD_SECONDS


class Command(BaseCommand):
    help = 'Check for power outage and mark devices offline if needed'

    def handle(self, *args, **options):
        system = SystemStatus.get_instance()
        now = timezone.now()

        time_since_last_heartbeat = (now - system.updated_at).total_seconds()

        if time_since_last_heartbeat > SYSTEM_HEARTBEAT_CHECK_SECONDS:
            self.stdout.write(self.style.WARNING(
                f'Power outage detected! System was offline for {time_since_last_heartbeat:.0f} seconds'
            ))

            # Find all devices that were online
            for device in Device.objects.select_related('user').all():
                last_change = device.state_changes.first()

                if last_change and last_change.status == 1:  # Was online
                    # Mark as offline at estimated time
                    offline_time = system.updated_at + timedelta(seconds=OFFLINE_THRESHOLD_SECONDS)

                    StateChange.objects.create(
                        device=device,
                        user=device.user,
                        timestamp=offline_time,
                        status=0  # went offline
                    )

                    self.stdout.write(
                        f'Marked {device.user.employee_name} offline at {offline_time}'
                    )
        else:
            self.stdout.write(self.style.SUCCESS('No power outage detected'))

        # Update system heartbeat
        system.save()

# Django On-Premise Agent - Technical Specification

## Overview

The Django agent runs on the local office network and is responsible for:
- Detecting device presence via IP ping
- Storing state changes locally in PostgreSQL
- Sending heartbeats to cloud (every 5 minutes)
- Sending hourly summaries to cloud (every 60 minutes)
- Providing Django Admin interface for device management
- Handling power outage detection and recovery

---

## Django Project Structure

```
agent/
├── monitoring/                 # Django app
│   ├── models.py              # Database models
│   ├── admin.py               # Django Admin configuration
│   ├── tasks.py               # Celery periodic tasks
│   ├── constants.py           # Configuration constants
│   ├── services.py            # Business logic (ping, cloud API)
│   └── management/
│       └── commands/
│           └── setup_system.py  # Initialize SystemStatus
├── config/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── celery.py             # Celery configuration
├── manage.py
├── requirements.txt
├── Dockerfile
└── .env                      # Environment variables
```

---

## Database Models

### Users Model
```python
# monitoring/models.py
from django.db import models

class User(models.Model):
    employee_name = models.CharField(max_length=100, unique=True)
    fake_name = models.CharField(max_length=100)
    display_order = models.IntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order']
        db_table = 'users'
    
    def __str__(self):
        return self.employee_name
    
    def is_online(self):
        """Check if user is currently online based on last state change"""
        last_change = self.state_changes.order_by('-timestamp').first()
        return last_change and last_change.status == 1
    
    def last_seen(self):
        """Get timestamp when user was last seen online"""
        last_online = self.state_changes.filter(status=1).order_by('-timestamp').first()
        return last_online.timestamp if last_online else None
```

### Devices Model
```python
class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    ip_address = models.GenericIPAddressField(unique=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    device_name = models.CharField(max_length=100, default='Primary Device')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'devices'
    
    def __str__(self):
        return f"{self.user.employee_name} - {self.ip_address}"
```

### StateChanges Model
```python
class StateChange(models.Model):
    STATUS_CHOICES = [
        (0, 'Went Offline'),
        (1, 'Went Online'),
    ]
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='state_changes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='state_changes')
    timestamp = models.DateTimeField()
    status = models.IntegerField(choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'state_changes'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['device', '-timestamp']),
        ]
    
    def __str__(self):
        status_text = 'online' if self.status == 1 else 'offline'
        return f"{self.user.employee_name} - {status_text} at {self.timestamp}"
```

### HourlySummary Model
```python
class HourlySummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hourly_summaries')
    hour = models.DateTimeField()  # Truncated to hour (minute=0, second=0)
    first_seen = models.DateTimeField(null=True)
    last_seen = models.DateTimeField(null=True)
    minutes_online = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'hourly_summaries'
        unique_together = ['user', 'hour']
        ordering = ['-hour']
    
    def __str__(self):
        return f"{self.user.employee_name} - {self.hour} ({self.minutes_online}min)"
```

### SystemStatus Model
```python
class SystemStatus(models.Model):
    # Always only one row (id=1)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_status'
    
    @classmethod
    def get_instance(cls):
        """Get or create the single SystemStatus instance"""
        obj, created = cls.objects.get_or_create(id=1)
        return obj
    
    def __str__(self):
        return f"System last active: {self.updated_at}"
```

---

## Configuration Constants

```python
# monitoring/constants.py

# Ping configuration
PING_INTERVAL_SECONDS = 60              # Ping devices every 1 minute
OFFLINE_THRESHOLD_SECONDS = 60          # Mark offline after 1 min of failed pings

# Cloud communication
HEARTBEAT_INTERVAL_MINUTES = 5          # Send "who's online" every 5 minutes
SUMMARY_INTERVAL_HOURS = 1              # Send hourly summary every hour

# System health
SYSTEM_HEARTBEAT_CHECK_SECONDS = 120    # Consider app crashed if no update in 2 min

# Cloud API
CLOUD_API_URL = os.getenv('CLOUD_API_URL', 'http://localhost:8080')
SITE_ID = os.getenv('SITE_ID', 'porto_office')
```

---

## Business Logic Services

### Ping Service
```python
# monitoring/services.py
import subprocess
import platform

def ping_device(ip_address, timeout=1):
    """
    Ping a device and return success/failure
    
    Args:
        ip_address: IP address to ping
        timeout: Timeout in seconds
    
    Returns:
        bool: True if ping successful, False otherwise
    """
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-W', str(timeout), ip_address]
    
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        print(f"Error pinging {ip_address}: {e}")
        return False
```

### Cloud API Service
```python
import requests
from django.conf import settings

def send_heartbeat(devices_online):
    """Send heartbeat to cloud API"""
    payload = {
        'site_id': settings.SITE_ID,
        'timestamp': timezone.now().isoformat(),
        'devices_online': devices_online
    }
    
    try:
        response = requests.post(
            f"{settings.CLOUD_API_URL}/api/heartbeat",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Error sending heartbeat: {e}")
        return False

def send_hourly_summary(summaries):
    """Send hourly summary to cloud API"""
    payload = {
        'site_id': settings.SITE_ID,
        'timestamp': timezone.now().isoformat(),
        'presence_data': summaries
    }
    
    try:
        response = requests.post(
            f"{settings.CLOUD_API_URL}/api/presence",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Error sending hourly summary: {e}")
        return False
```

---

## Celery Periodic Tasks

### Setup
```python
# config/celery.py
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('agent')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'ping-devices': {
        'task': 'monitoring.tasks.ping_all_devices',
        'schedule': 60.0,  # Every 60 seconds
    },
    'send-heartbeat': {
        'task': 'monitoring.tasks.send_heartbeat_to_cloud',
        'schedule': 300.0,  # Every 5 minutes
    },
    'send-hourly-summary': {
        'task': 'monitoring.tasks.send_hourly_summary_to_cloud',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    'update-system-heartbeat': {
        'task': 'monitoring.tasks.update_system_heartbeat',
        'schedule': 30.0,  # Every 30 seconds
    },
}
```

### Task 1: Ping All Devices
```python
# monitoring/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Device, StateChange, User
from .services import ping_device
from .constants import OFFLINE_THRESHOLD_SECONDS

# In-memory tracker for failed pings
device_failure_tracker = {}

@shared_task
def ping_all_devices():
    """Ping all active devices and update state changes"""
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
        else:
            # Ping failed
            if device.id not in device_failure_tracker:
                # First failure - start tracking
                device_failure_tracker[device.id] = timezone.now()
            else:
                # Check if threshold reached
                time_failing = (timezone.now() - device_failure_tracker[device.id]).total_seconds()
                
                if time_failing >= OFFLINE_THRESHOLD_SECONDS:
                    # Mark offline (only if was online)
                    if last_change and last_change.status == 1:
                        StateChange.objects.create(
                            device=device,
                            user=device.user,
                            timestamp=timezone.now(),
                            status=0  # went offline
                        )
                    # Clear tracker
                    device_failure_tracker.pop(device.id, None)
```

### Task 2: Send Heartbeat
```python
@shared_task
def send_heartbeat_to_cloud():
    """Send current online status to cloud"""
    devices_online = []
    
    for user in User.objects.all():
        if user.is_online():
            devices_online.append({
                'employee_id': user.id,
                'employee_name': user.employee_name,
                'fake_name': user.fake_name,
                'area': 'default'  # Hardcoded for MVP
            })
    
    from .services import send_heartbeat
    send_heartbeat(devices_online)
```

### Task 3: Generate and Send Hourly Summary
```python
from .models import HourlySummary
from datetime import timedelta

@shared_task
def send_hourly_summary_to_cloud():
    """Calculate hourly summary and send to cloud"""
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
                        minutes_online += (change.timestamp - online_start).total_seconds() / 60
                        last_seen = change.timestamp
                        online_start = None
            
            # If still online at end of hour
            if online_start:
                minutes_online += (end_time - online_start).total_seconds() / 60
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
        from .services import send_hourly_summary
        send_hourly_summary(summaries)
```

### Task 4: Update System Heartbeat
```python
@shared_task
def update_system_heartbeat():
    """Update system heartbeat to track app health"""
    from .models import SystemStatus
    system = SystemStatus.get_instance()
    system.save()  # This updates updated_at automatically
```

---

## Power Outage Detection

### On Startup
```python
# monitoring/management/commands/check_outage.py
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
```

**Run on startup**:
```bash
python manage.py check_outage
```

---

## Django Admin Configuration

```python
# monitoring/admin.py
from django.contrib import admin
from .models import User, Device, StateChange, HourlySummary, SystemStatus

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['employee_name', 'fake_name', 'display_order', 'is_online_status', 'created_at']
    list_editable = ['display_order']
    search_fields = ['employee_name', 'fake_name']
    ordering = ['display_order']
    
    def is_online_status(self, obj):
        return '🟢 Online' if obj.is_online() else '⚫ Offline'
    is_online_status.short_description = 'Status'

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'mac_address', 'device_name', 'created_at']
    list_filter = ['user']
    search_fields = ['ip_address', 'mac_address', 'user__employee_name']

@admin.register(StateChange)
class StateChangeAdmin(admin.ModelAdmin):
    list_display = ['user', 'device', 'timestamp', 'status', 'created_at']
    list_filter = ['status', 'user']
    date_hierarchy = 'timestamp'
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # State changes auto-generated

@admin.register(HourlySummary)
class HourlySummaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'hour', 'first_seen', 'last_seen', 'minutes_online']
    list_filter = ['user']
    date_hierarchy = 'hour'
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # Summaries auto-generated

@admin.register(SystemStatus)
class SystemStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'updated_at']
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        return False  # Only one instance allowed
    
    def has_delete_permission(self, request, obj=None):
        return False  # Cannot delete system status
```

---

## Environment Variables

```bash
# .env

# Django settings
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_NAME=presence_monitor
DATABASE_USER=postgres
DATABASE_PASSWORD=your-db-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Celery / Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Cloud API
CLOUD_API_URL=https://your-cloud-backend.com
SITE_ID=porto_office

# System
TZ=Europe/Lisbon
```

---

## Setup Instructions

### 1. Install Dependencies
```bash
cd agent/
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Setup Database
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 3. Initialize System Status
```bash
python manage.py shell
>>> from monitoring.models import SystemStatus
>>> SystemStatus.get_instance()
>>> exit()
```

### 4. Run Services
```bash
# Terminal 1: Django
python manage.py runserver 0.0.0.0:8000

# Terminal 2: Celery Worker
celery -A config worker -l info

# Terminal 3: Celery Beat
celery -A config beat -l info
```

### 5. Access Django Admin
```
http://localhost:8000/admin
```

---

## Testing

### Manual Testing
1. Add user in Django Admin (e.g., "Ricardo_Silva" / "Employee_Alpha")
2. Add device with valid IP on local network
3. Check state changes in admin after 1-2 minutes
4. Disconnect device from network
5. Verify offline state change after OFFLINE_THRESHOLD

### Monitor Logs
```bash
# Watch Celery logs
celery -A config worker -l debug

# Check task execution
celery -A config inspect active
celery -A config inspect scheduled
```

---

## Related Documents
- [01-system-architecture.md](./01-system-architecture.md) - System overview
- [03-spring-boot-backend.md](./03-spring-boot-backend.md) - Cloud backend
- [05-deployment.md](./05-deployment.md) - Deployment guide

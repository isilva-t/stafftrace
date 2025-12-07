from django.db import models


class User(models.Model):
    """Employee/User model with real and fake names."""
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
        """Check if user is currently online based on last state change."""
        last_change = self.state_changes.order_by('-timestamp').first()
        return last_change and last_change.status == 1

    def last_seen(self):
        """Get timestamp when user was last seen online."""
        last_online = self.state_changes.filter(status=1).order_by('-timestamp').first()
        return last_online.timestamp if last_online else None


class Device(models.Model):
    """Device model - each user can have multiple devices."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    ip_address = models.GenericIPAddressField(unique=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    device_name = models.CharField(max_length=100, default='Primary Device')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'devices'

    def __str__(self):
        return f"{self.user.employee_name} - {self.ip_address}"


class StateChange(models.Model):
    """State change model - records when devices go online/offline."""
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


class HourlySummary(models.Model):
    """Hourly summary model - aggregated presence data per hour."""
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


class SystemStatus(models.Model):
    """System status model - single row to track system heartbeat."""
    # Always only one row (id=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_status'

    @classmethod
    def get_instance(cls):
        """Get or create the single SystemStatus instance."""
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return f"System last active: {self.updated_at}"

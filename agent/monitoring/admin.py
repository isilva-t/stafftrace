"""
Django Admin configuration for monitoring app.
"""
from django.contrib import admin
from .models import User, Device, StateChange, HourlySummary, SystemStatus, AgentDowntime


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['employee_name', 'fake_name',
                    'display_order', 'is_online_status', 'created_at']
    list_editable = ['display_order']
    search_fields = ['employee_name', 'fake_name']
    ordering = ['display_order']

    def is_online_status(self, obj):
        return '🟢 Online' if obj.is_online() else '🔴 Offline'
    is_online_status.short_description = 'Status'


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address',
                    'mac_address', 'device_name', 'created_at']
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
    list_display = ['user', 'hour', 'first_seen',
                    'last_seen', 'minutes_online']
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


@admin.register(AgentDowntime)
class AgentDowntimeAdmin(admin.ModelAdmin):
    list_display = ["downtime_start", "downtime_end",
                    "duration_minutes", "synced", "created_at"]
    readonly_fields = ['created_at']
    ordering = ["-downtime_start"]

    def duration_minutes(self, obj):
        duration = (obj.downtime_end - obj.downtime_start).total_seconds() / 60
        return f"{duration:.0f} min"
    duration_minutes.short_description = "Duration"

    def has_add_permission(self, request):
        return False

from django.contrib import admin

from .models import Command, Device, Event, Telemetry


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "hardware_id", "firmware_version", "is_active", "last_seen_at")
    search_fields = ("name", "hardware_id")


@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    list_display = ("device", "topic", "temperature", "recorded_at")
    list_filter = ("topic", "recorded_at")
    search_fields = ("device__name", "device__hardware_id")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("device", "level", "message", "created_at")
    list_filter = ("level", "created_at")


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ("device", "command", "status", "created_at", "updated_at")
    list_filter = ("status",)

from django.db import models
from django.utils import timezone


class Device(models.Model):
    name = models.CharField(max_length=120)
    hardware_id = models.CharField(max_length=64, unique=True)
    firmware_version = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.hardware_id})"

    @property
    def is_online(self) -> bool:
        if not self.last_seen_at:
            return False
        return self.last_seen_at >= timezone.now() - timezone.timedelta(minutes=5)


class Telemetry(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="telemetries")
    topic = models.CharField(max_length=255)
    payload = models.JSONField(default=dict, blank=True)
    temperature = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self) -> str:
        return f"{self.device.name} @ {self.recorded_at:%Y-%m-%d %H:%M:%S}"


class Event(models.Model):
    LEVEL_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("error", "Error"),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="events")
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES, default="info")
    message = models.CharField(max_length=255)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]


class Command(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("ack", "Ack"),
        ("failed", "Failed"),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="commands")
    command = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

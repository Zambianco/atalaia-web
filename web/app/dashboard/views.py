from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import Device, Event, Telemetry


@login_required
def dashboard_view(request):
    devices = Device.objects.all()
    online_count = sum(1 for device in devices if device.is_online)
    latest_telemetries = Telemetry.objects.select_related("device")[:10]
    recent_events = Event.objects.select_related("device")[:10]

    context = {
        "device_count": devices.count(),
        "online_count": online_count,
        "offline_count": devices.count() - online_count,
        "latest_telemetries": latest_telemetries,
        "recent_events": recent_events,
        "device_topics": Telemetry.objects.values("topic").annotate(total=Count("id")).order_by("-total")[:5],
    }
    return render(request, "dashboard/index.html", context)


@login_required
def device_list_view(request):
    devices = Device.objects.all()
    return render(request, "dashboard/devices.html", {"devices": devices})


@login_required
def device_detail_view(request, pk):
    device = get_object_or_404(Device, pk=pk)
    telemetries = list(device.telemetries.all()[:25])
    latest_telemetry = telemetries[0] if telemetries else None
    chart_telemetries = list(
        device.telemetries.exclude(temperature__isnull=True).order_by("-recorded_at")[:20]
    )
    chart_telemetries.reverse()
    events = device.events.all()[:25]
    return render(
        request,
        "dashboard/device_detail.html",
        {
            "device": device,
            "telemetries": telemetries,
            "latest_telemetry": latest_telemetry,
            "chart_labels": [item.recorded_at.strftime("%d/%m %H:%M:%S") for item in chart_telemetries],
            "chart_values": [float(item.temperature) for item in chart_telemetries],
            "events": events,
        },
    )

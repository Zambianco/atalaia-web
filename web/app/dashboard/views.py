from datetime import datetime, timedelta, time

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, CharField, Count, F, Max, Min, Value
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.utils import timezone

from .models import Device, Event, Telemetry


def _get_history_window(request):
    period = request.GET.get("period", "7d")
    now = timezone.now()
    start = now - timedelta(days=7)
    end = now

    if period == "24h":
        start = now - timedelta(days=1)
    elif period == "30d":
        start = now - timedelta(days=30)
    elif period == "custom":
        from_date = parse_date(request.GET.get("from") or "")
        to_date = parse_date(request.GET.get("to") or "")

        if from_date:
            start = timezone.make_aware(datetime.combine(from_date, time.min))
        if to_date:
            end = timezone.make_aware(datetime.combine(to_date + timedelta(days=1), time.min))

    return period, start, end


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
            "chart_labels": [
                timezone.localtime(item.recorded_at).strftime("%d/%m %H:%M:%S")
                for item in chart_telemetries
            ],
            "chart_values": [float(item.temperature) for item in chart_telemetries],
            "events": events,
        },
    )


@login_required
def history_view(request):
    devices = Device.objects.all()
    selected_device = request.GET.get("device", "").strip()
    selected_kind = request.GET.get("kind", "all").strip()
    period, start, end = _get_history_window(request)

    telemetry_qs = Telemetry.objects.select_related("device")
    event_qs = Event.objects.select_related("device")

    if selected_device.isdigit():
        telemetry_qs = telemetry_qs.filter(device_id=selected_device)
        event_qs = event_qs.filter(device_id=selected_device)

    telemetry_qs = telemetry_qs.filter(recorded_at__gte=start, recorded_at__lt=end)
    event_qs = event_qs.filter(created_at__gte=start, created_at__lt=end)

    telemetry_stats = telemetry_qs.aggregate(
        total=Count("id"),
        min_temperature=Min("temperature"),
        avg_temperature=Avg("temperature"),
        max_temperature=Max("temperature"),
    )
    chart_telemetries = list(
        telemetry_qs.exclude(temperature__isnull=True).order_by("recorded_at")[:200]
    )
    event_total = event_qs.count()

    telemetry_rows = telemetry_qs.annotate(
        kind=Value("telemetria", output_field=CharField()),
        timestamp=F("recorded_at"),
        device_name=F("device__name"),
        hardware_id=F("device__hardware_id"),
        primary=F("topic"),
        secondary=Cast("temperature", output_field=CharField()),
    ).values("kind", "timestamp", "device_id", "device_name", "hardware_id", "primary", "secondary")

    event_rows = event_qs.annotate(
        kind=Value("evento", output_field=CharField()),
        timestamp=F("created_at"),
        device_name=F("device__name"),
        hardware_id=F("device__hardware_id"),
        primary=F("level"),
        secondary=F("message"),
    ).values("kind", "timestamp", "device_id", "device_name", "hardware_id", "primary", "secondary")

    if selected_kind == "telemetry":
        history_rows = telemetry_rows
    elif selected_kind == "event":
        history_rows = event_rows
    else:
        history_rows = telemetry_rows.union(event_rows, all=True)

    history_rows = history_rows.order_by("-timestamp", "-device_name")

    context = {
        "devices": devices,
        "history_rows": history_rows,
        "history_total": history_rows.count(),
        "period": period,
        "from_value": request.GET.get("from", ""),
        "to_value": request.GET.get("to", ""),
        "selected_device": selected_device,
        "selected_kind": selected_kind,
        "start": start,
        "end": end,
        "telemetry_total": telemetry_stats["total"] or 0,
        "min_temperature": telemetry_stats["min_temperature"],
        "avg_temperature": telemetry_stats["avg_temperature"],
        "max_temperature": telemetry_stats["max_temperature"],
        "event_total": event_total,
        "chart_labels": [
            timezone.localtime(item.recorded_at).strftime("%d/%m %H:%M:%S")
            for item in chart_telemetries
        ],
        "chart_values": [float(item.temperature) for item in chart_telemetries],
    }
    return render(request, "dashboard/history.html", context)

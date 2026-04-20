from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ActivityForm, AppointmentForm, LoginForm, MetricForm, ProfileUpdateForm, RegistrationForm
from .models import ActivityEntry, Appointment, HealthMetric, Profile


def landing(request):
    return render(request, "pages/index.html")


def about(request):
    return render(request, "pages/about.html")


def how_to_use(request):
    return render(request, "pages/howto.html")


def _calculate_bmi(height_cm, weight_kg):
    if not height_cm or not weight_kg:
        return None
    try:
        height_m = Decimal(height_cm) / Decimal("100")
        bmi = Decimal(weight_kg) / (height_m * height_m)
        return bmi.quantize(Decimal("0.1"))
    except (InvalidOperation, ZeroDivisionError):
        return None


def _bmi_status(bmi):
    if bmi is None:
        return "necunoscut"
    if bmi < Decimal("18.5"):
        return "subponderal"
    if bmi < Decimal("25"):
        return "în regulă"
    if bmi < Decimal("30"):
        return "supraponderal"
    return "obezitate"


def _bmi_position(bmi):
    if bmi is None:
        return "44%"
    value = float(bmi)
    value = max(15.0, min(40.0, value))
    percent = (value - 15.0) / 25.0 * 100
    return f"{percent:.0f}%"


def _blood_sugar_status(value):
    if value is None:
        return "N/A"
    if value < 70:
        return "Scăzut"
    if value <= 100:
        return "Normal"
    return "Ridicat"


def _bpm_status(value):
    if value is None:
        return "N/A"
    if value < 60:
        return "Scăzut"
    if value <= 100:
        return "Normal"
    return "Ridicat"


def _bp_status(sys_value, dia_value):
    if sys_value is None or dia_value is None:
        return "N/A"
    if sys_value < 120 and dia_value < 80:
        return "Normal"
    if sys_value < 130 and dia_value < 80:
        return "Pre-HTA"
    return "Ridicat"


def _activity_series(user):
    today = timezone.localdate()
    start_date = today - timedelta(days=11)
    date_list = [start_date + timedelta(days=i) for i in range(12)]
    entries = ActivityEntry.objects.filter(user=user, date__range=(start_date, today))
    by_date = {entry.date: entry for entry in entries}
    series = []
    for date_item in date_list:
        entry = by_date.get(date_item)
        if entry:
            series.append(
                {
                    "label": date_item.strftime("%b %d"),
                    "aerobics": entry.aerobics,
                    "yoga": entry.yoga,
                    "meditation": entry.meditation,
                }
            )
        else:
            series.append({"label": date_item.strftime("%b %d"), "aerobics": 0, "yoga": 0, "meditation": 0})
    return series


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            email = form.cleaned_data["email"]
            user = User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data["password"],
            )
            profile = Profile.objects.create(
                user=user,
                age=form.cleaned_data["age"],
                gender=form.cleaned_data["gender"],
                height_cm=form.cleaned_data["height_cm"],
                weight_kg=form.cleaned_data["weight_kg"],
            )
            bmi = _calculate_bmi(profile.height_cm, profile.weight_kg)
            if bmi is not None:
                profile.bmi = bmi
                profile.save(update_fields=["bmi"])
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "pages/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            return redirect("dashboard")
    else:
        form = LoginForm()
    return render(request, "pages/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("landing")


@login_required
def dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile_form = ProfileUpdateForm(instance=profile)
    metric_form = MetricForm()
    activity_form = ActivityForm()
    appointment_form = AppointmentForm()

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "profile":
            profile_form = ProfileUpdateForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile = profile_form.save(commit=False)
                profile.bmi = _calculate_bmi(profile.height_cm, profile.weight_kg)
                profile.save()
                return redirect("dashboard")
        elif form_type == "metrics":
            metric_form = MetricForm(request.POST)
            if metric_form.is_valid():
                metric = metric_form.save(commit=False)
                metric.user = request.user
                metric.save()
                return redirect("dashboard")
        elif form_type == "activity":
            activity_form = ActivityForm(request.POST)
            if activity_form.is_valid():
                activity = activity_form.save(commit=False)
                activity.user = request.user
                activity.save()
                return redirect("dashboard")
        elif form_type == "appointment":
            appointment_form = AppointmentForm(request.POST)
            if appointment_form.is_valid():
                appointment = appointment_form.save(commit=False)
                appointment.user = request.user
                appointment.save()
                return redirect("dashboard")

    latest_metric = HealthMetric.objects.filter(user=request.user).first()
    metrics = {
        "blood_sugar": latest_metric.blood_sugar_mg if latest_metric else None,
        "bpm": latest_metric.bpm if latest_metric else None,
        "bp_sys": latest_metric.blood_pressure_sys if latest_metric else None,
        "bp_dia": latest_metric.blood_pressure_dia if latest_metric else None,
    }

    bmi_value = profile.bmi
    bmi_status = _bmi_status(bmi_value)
    bmi_position = _bmi_position(bmi_value)
    activity_series = _activity_series(request.user)
    appointments = Appointment.objects.filter(user=request.user)[:3]

    context = {
        "profile": profile,
        "bmi_status": bmi_status,
        "bmi_position": bmi_position,
        "profile_form": profile_form,
        "metric_form": metric_form,
        "activity_form": activity_form,
        "appointment_form": appointment_form,
        "metrics": metrics,
        "blood_sugar_status": _blood_sugar_status(metrics["blood_sugar"]),
        "bpm_status": _bpm_status(metrics["bpm"]),
        "bp_status": _bp_status(metrics["bp_sys"], metrics["bp_dia"]),
        "activity_series": activity_series,
        "appointments": appointments,
    }
    return render(request, "pages/dashboard.html", context)

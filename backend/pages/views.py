import calendar
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import (
    ActivityForm,
    AppointmentForm,
    FoodEntryForm,
    GoalForm,
    LoginForm,
    MetricForm,
    ProfileUpdateForm,
    RegistrationForm,
    SleepLogForm,
    WaterLogForm,
)
from .models import ActivityEntry, Appointment, FoodEntry, Goal, HealthMetric, Profile, SleepLog, WaterLog

MONTH_NAMES_RO = {
    1: "Ianuarie",
    2: "Februarie",
    3: "Martie",
    4: "Aprilie",
    5: "Mai",
    6: "Iunie",
    7: "Iulie",
    8: "August",
    9: "Septembrie",
    10: "Octombrie",
    11: "Noiembrie",
    12: "Decembrie",
}

MONTH_NAMES_RO_SHORT = {
    1: "ian",
    2: "feb",
    3: "mar",
    4: "apr",
    5: "mai",
    6: "iun",
    7: "iul",
    8: "aug",
    9: "sep",
    10: "oct",
    11: "noi",
    12: "dec",
}


def landing(request):
    return render(request, "pages/index.html")


def about(request):
    return render(request, "pages/about.html")


def how_to_use(request):
    return render(request, "pages/howto.html")


@login_required
def nutrition(request):
    selected_date = _parse_selected_date(request)
    redirect_target = f"{request.path}?date={selected_date.isoformat()}"
    meal_order = [
        ("breakfast", "Mic dejun", "morning"),
        ("lunch", "Prânz", "midday"),
        ("dinner", "Cina", "night"),
        ("snacks", "Gustari", "snack"),
    ]
    meal_forms = {meal_key: FoodEntryForm(initial={"meal_type": meal_key}) for meal_key, _, _ in meal_order}

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_food":
            add_form = FoodEntryForm(request.POST)
            if add_form.is_valid():
                entry = add_form.save(commit=False)
                entry.user = request.user
                entry.date = selected_date
                entry.save()
                return redirect(redirect_target)
            meal_key = request.POST.get("meal_type")
            if meal_key in meal_forms:
                meal_forms[meal_key] = add_form
        elif action == "delete_food":
            entry_id = request.POST.get("entry_id")
            FoodEntry.objects.filter(id=entry_id, user=request.user, date=selected_date).delete()
            return redirect(redirect_target)

    entries = list(
        FoodEntry.objects.filter(user=request.user, date=selected_date)
        .order_by("created_at")
    )

    by_meal = {meal_key: [] for meal_key, _, _ in meal_order}
    for entry in entries:
        by_meal[entry.meal_type].append(entry)

    total_calories = sum(entry.calories for entry in entries)
    total_protein = sum((entry.protein_g for entry in entries), Decimal("0"))
    total_carbs = sum((entry.carbs_g for entry in entries), Decimal("0"))
    total_fat = sum((entry.fat_g for entry in entries), Decimal("0"))

    calories_summary = _macro_summary(total_calories, NUTRITION_GOALS["calories"])
    protein_summary = _macro_summary(total_protein, NUTRITION_GOALS["protein"])
    carbs_summary = _macro_summary(total_carbs, NUTRITION_GOALS["carbs"])
    fat_summary = _macro_summary(total_fat, NUTRITION_GOALS["fat"])

    protein_kcal = float(total_protein) * 4
    carbs_kcal = float(total_carbs) * 4
    fat_kcal = float(total_fat) * 9
    breakdown_total = protein_kcal + carbs_kcal + fat_kcal
    if breakdown_total > 0:
        protein_pct = round((protein_kcal / breakdown_total) * 100)
        carbs_pct = round((carbs_kcal / breakdown_total) * 100)
        fat_pct = max(0, 100 - protein_pct - carbs_pct)
    else:
        protein_pct = carbs_pct = fat_pct = 0

    donut_style = (
        f"conic-gradient(#4f7cff 0 {protein_pct}%, "
        f"#4fb987 {protein_pct}% {protein_pct + carbs_pct}%, "
        f"#8b6cff {protein_pct + carbs_pct}% 100%)"
    )

    fiber_goal = Decimal("25")
    sugar_goal = Decimal("50")
    sodium_goal = Decimal("2300")
    fiber_value = (total_carbs * Decimal("0.14")).quantize(Decimal("0.1"))
    sugar_value = (total_carbs * Decimal("0.30")).quantize(Decimal("0.1"))
    sodium_value = Decimal(int(total_calories * 0.75))

    meal_cards = []
    for meal_key, meal_label, meal_tone in meal_order:
        meal_entries = by_meal[meal_key]
        meal_cards.append(
            {
                "key": meal_key,
                "label": meal_label,
                "tone": meal_tone,
                "calories": sum(item.calories for item in meal_entries),
                "entries": meal_entries,
                "form": meal_forms[meal_key],
            }
        )

    context = {
        "selected_date": selected_date,
        "selected_date_iso": selected_date.isoformat(),
        "totals": {
            "calories": calories_summary,
            "protein": protein_summary,
            "carbs": carbs_summary,
            "fat": fat_summary,
        },
        "meal_cards": meal_cards,
        "breakdown": {
            "protein_kcal": int(round(protein_kcal)),
            "carbs_kcal": int(round(carbs_kcal)),
            "fat_kcal": int(round(fat_kcal)),
            "protein_pct": protein_pct,
            "carbs_pct": carbs_pct,
            "fat_pct": fat_pct,
            "donut_style": donut_style,
        },
        "other_nutrients": {
            "fiber": {
                "value": fiber_value,
                "goal": fiber_goal,
                "percent": _goal_percent(fiber_value, fiber_goal),
            },
            "sugar": {
                "value": sugar_value,
                "goal": sugar_goal,
                "percent": _goal_percent(sugar_value, sugar_goal),
            },
            "sodium": {
                "value": sodium_value,
                "goal": sodium_goal,
                "percent": _goal_percent(sodium_value, sodium_goal),
            },
        },
    }
    return render(request, "pages/nutrition.html", context)


@login_required
def profile_page(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile_form = ProfileUpdateForm(instance=profile)

    if request.method == "POST":
        profile_form = ProfileUpdateForm(request.POST, instance=profile)
        if profile_form.is_valid():
            profile = profile_form.save(commit=False)
            profile.bmi = _calculate_bmi(profile.height_cm, profile.weight_kg)
            profile.save()
            return redirect("profile")

    latest_metric = HealthMetric.objects.filter(user=request.user).first()
    metrics_history = HealthMetric.objects.filter(user=request.user)[:8]

    context = {
        "profile": profile,
        "profile_form": profile_form,
        "latest_metric": latest_metric,
        "metrics_history": metrics_history,
        "bmi_status": _bmi_status(profile.bmi),
    }
    return render(request, "pages/profile.html", context)


@login_required
def goals_page(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    goal, _ = Goal.objects.get_or_create(user=request.user)
    goal_form = GoalForm(instance=goal)

    if request.method == "POST":
        goal_form = GoalForm(request.POST, instance=goal)
        if goal_form.is_valid():
            goal_form.save()
            return redirect("goals")

    today = timezone.localdate()
    water_today = WaterLog.objects.filter(user=request.user, date=today).first()
    sleep_today = SleepLog.objects.filter(user=request.user, date=today).first()
    activity_today = ActivityEntry.objects.filter(user=request.user, date=today).first()

    activity_value = 0
    if activity_today:
        activity_value = round((activity_today.aerobics + activity_today.yoga + activity_today.meditation) / 3)

    current_weight = profile.weight_kg or Decimal("0")
    target_weight = goal.target_weight_kg or Decimal("0")
    weight_gap = None
    if target_weight and current_weight:
        weight_gap = abs(current_weight - target_weight).quantize(Decimal("0.1"))

    context = {
        "goal_form": goal_form,
        "goal": goal,
        "profile": profile,
        "today": today,
        "summary": {
            "water": water_today.amount_ml if water_today else 0,
            "sleep": sleep_today.hours if sleep_today else Decimal("0"),
            "activity": activity_value,
            "bmi": profile.bmi or Decimal("0"),
            "weight_gap": weight_gap,
        },
        "progress": {
            "water": _goal_percent(water_today.amount_ml if water_today else 0, goal.water_goal_ml),
            "sleep": _goal_percent(sleep_today.hours if sleep_today else Decimal("0"), goal.sleep_goal_hours),
            "activity": _goal_percent(activity_value, goal.activity_goal_percent),
            "bmi": _goal_percent(profile.bmi if profile.bmi else Decimal("0"), goal.target_bmi if goal.target_bmi else Decimal("0")),
        },
    }
    return render(request, "pages/goals.html", context)


@login_required
def habits_page(request):
    selected_date = _parse_selected_date(request)
    water_form = WaterLogForm(initial={"date": selected_date})
    sleep_form = SleepLogForm(initial={"date": selected_date})

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "water":
            water_form = WaterLogForm(request.POST)
            if water_form.is_valid():
                log_date = water_form.cleaned_data["date"]
                WaterLog.objects.update_or_create(
                    user=request.user,
                    date=log_date,
                    defaults={"amount_ml": water_form.cleaned_data["amount_ml"]},
                )
                return redirect(f"{request.path}?date={log_date.isoformat()}")
        elif form_type == "sleep":
            sleep_form = SleepLogForm(request.POST)
            if sleep_form.is_valid():
                log_date = sleep_form.cleaned_data["date"]
                SleepLog.objects.update_or_create(
                    user=request.user,
                    date=log_date,
                    defaults={"hours": sleep_form.cleaned_data["hours"]},
                )
                return redirect(f"{request.path}?date={log_date.isoformat()}")

    goal, _ = Goal.objects.get_or_create(user=request.user)
    selected_water = WaterLog.objects.filter(user=request.user, date=selected_date).first()
    selected_sleep = SleepLog.objects.filter(user=request.user, date=selected_date).first()

    week_dates = [selected_date - timedelta(days=i) for i in range(6, -1, -1)]
    water_logs = WaterLog.objects.filter(user=request.user, date__range=(week_dates[0], week_dates[-1]))
    sleep_logs = SleepLog.objects.filter(user=request.user, date__range=(week_dates[0], week_dates[-1]))
    water_by_date = {entry.date: entry.amount_ml for entry in water_logs}
    sleep_by_date = {entry.date: entry.hours for entry in sleep_logs}

    weekly_series = []
    for date_item in week_dates:
        weekly_series.append(
            {
                "label": date_item.strftime("%d.%m"),
                "water": water_by_date.get(date_item, 0),
                "sleep": sleep_by_date.get(date_item, Decimal("0")),
            }
        )

    total_water = sum(item["water"] for item in weekly_series)
    total_sleep = sum((item["sleep"] for item in weekly_series), Decimal("0"))
    water_avg = round(total_water / 7) if weekly_series else 0
    sleep_avg = (total_sleep / Decimal("7")).quantize(Decimal("0.1")) if weekly_series else Decimal("0")

    context = {
        "selected_date": selected_date,
        "selected_date_iso": selected_date.isoformat(),
        "water_form": water_form,
        "sleep_form": sleep_form,
        "goal": goal,
        "selected": {
            "water": selected_water.amount_ml if selected_water else 0,
            "sleep": selected_sleep.hours if selected_sleep else Decimal("0"),
        },
        "weekly_series": weekly_series,
        "weekly_avg": {"water": water_avg, "sleep": sleep_avg},
        "progress": {
            "water": _goal_percent(selected_water.amount_ml if selected_water else 0, goal.water_goal_ml),
            "sleep": _goal_percent(selected_sleep.hours if selected_sleep else Decimal("0"), goal.sleep_goal_hours),
        },
    }
    return render(request, "pages/habits.html", context)


@login_required
def history_page(request):
    appointment_form = AppointmentForm(initial={"date": timezone.localdate()})

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "delete_metric":
            metric_id = request.POST.get("metric_id")
            HealthMetric.objects.filter(id=metric_id, user=request.user).delete()
            return redirect("history")
        if action == "delete_appointment":
            appointment_id = request.POST.get("appointment_id")
            Appointment.objects.filter(id=appointment_id, user=request.user).delete()
            return redirect("history")
        if action == "delete_food":
            entry_id = request.POST.get("entry_id")
            FoodEntry.objects.filter(id=entry_id, user=request.user).delete()
            return redirect("history")
        if action == "add_appointment":
            appointment_form = AppointmentForm(request.POST)
            if appointment_form.is_valid():
                appointment = appointment_form.save(commit=False)
                appointment.user = request.user
                appointment.save()
                return redirect("history")

    metrics = HealthMetric.objects.filter(user=request.user).order_by("-created_at")[:40]
    appointments = Appointment.objects.filter(user=request.user).order_by("date")
    food_entries = FoodEntry.objects.filter(user=request.user).order_by("-date", "-created_at")[:40]
    food_daily = (
        FoodEntry.objects.filter(user=request.user)
        .values("date")
        .annotate(
            calories=Sum("calories"),
            protein=Sum("protein_g"),
            carbs=Sum("carbs_g"),
            fat=Sum("fat_g"),
        )
        .order_by("-date")[:14]
    )

    context = {
        "metrics": metrics,
        "appointments": appointments,
        "food_entries": food_entries,
        "food_daily": food_daily,
        "appointment_form": appointment_form,
    }
    return render(request, "pages/history.html", context)


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
        return "Fără date"
    if value < 70:
        return "Scăzut"
    if value <= 100:
        return "Normal"
    return "Ridicat"


def _bpm_status(value):
    if value is None:
        return "Fără date"
    if value < 60:
        return "Scăzut"
    if value <= 100:
        return "Normal"
    return "Ridicat"


def _bp_status(sys_value, dia_value):
    if sys_value is None or dia_value is None:
        return "Fără date"
    if sys_value < 120 and dia_value < 80:
        return "Normal"
    if sys_value < 130 and dia_value < 80:
        return "Pre-HTA"
    return "Ridicat"


def _activity_series(user, month_start):
    month_days = calendar.monthrange(month_start.year, month_start.month)[1]
    month_end = month_start.replace(day=month_days)
    date_list = [month_start + timedelta(days=i) for i in range(month_days)]
    entries = ActivityEntry.objects.filter(user=user, date__range=(month_start, month_end))
    by_date = {entry.date: entry for entry in entries}
    series = []
    for date_item in date_list:
        entry = by_date.get(date_item)
        if entry:
            series.append(
                {
                    "label": _short_date_label_ro(date_item),
                    "aerobics": entry.aerobics,
                    "yoga": entry.yoga,
                    "meditation": entry.meditation,
                }
            )
        else:
            series.append({"label": _short_date_label_ro(date_item), "aerobics": 0, "yoga": 0, "meditation": 0})
    return series


def _month_name_ro(date_value):
    return MONTH_NAMES_RO.get(date_value.month, "")


def _short_date_label_ro(date_value):
    return f"{date_value.day:02d} {MONTH_NAMES_RO_SHORT.get(date_value.month, '')}"


def _parse_activity_month(request):
    raw = request.GET.get("month") or request.POST.get("month")
    today = timezone.localdate()
    default_month = today.replace(day=1)
    if not raw:
        return default_month
    try:
        selected = datetime.strptime(raw, "%Y-%m").date()
        return selected.replace(day=1)
    except ValueError:
        return default_month


def _activity_month_options(selected_month, count=12):
    options = []
    cursor = timezone.localdate().replace(day=1)
    for _ in range(count):
        value = cursor.strftime("%Y-%m")
        options.append(
            {
                "value": value,
                "label": f"{_month_name_ro(cursor)} {cursor.year}",
                "selected": cursor.year == selected_month.year and cursor.month == selected_month.month,
            }
        )
        cursor = _shift_month(cursor, -1)

    if not any(option["selected"] for option in options):
        options.insert(
            0,
            {
                "value": selected_month.strftime("%Y-%m"),
                "label": f"{_month_name_ro(selected_month)} {selected_month.year}",
                "selected": True,
            },
        )
    return options


def _shift_month(date_value, delta):
    month_index = (date_value.year * 12 + date_value.month - 1) + delta
    year, month_zero = divmod(month_index, 12)
    return date_value.replace(year=year, month=month_zero + 1, day=1)


NUTRITION_GOALS = {
    "calories": 2000,
    "protein": Decimal("150"),
    "carbs": Decimal("250"),
    "fat": Decimal("67"),
}


def _parse_selected_date(request):
    raw = request.GET.get("date") or request.POST.get("date")
    if not raw:
        return timezone.localdate()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return timezone.localdate()


def _goal_percent(value, goal):
    if goal in (0, Decimal("0")):
        return 0
    percent = (Decimal(value) / Decimal(goal)) * 100
    return int(min(100, max(0, round(percent))))


def _macro_summary(total, goal):
    return {
        "value": total,
        "goal": goal,
        "percent": _goal_percent(total, goal),
        "left": max(0, Decimal(goal) - Decimal(total)),
    }


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
    selected_month = _parse_activity_month(request)
    selected_month_value = selected_month.strftime("%Y-%m")
    redirect_target = f"{request.path}?month={selected_month_value}"

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "profile":
            profile_form = ProfileUpdateForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile = profile_form.save(commit=False)
                profile.bmi = _calculate_bmi(profile.height_cm, profile.weight_kg)
                profile.save()
                return redirect(redirect_target)
        elif form_type == "metrics":
            metric_form = MetricForm(request.POST)
            if metric_form.is_valid():
                metric = metric_form.save(commit=False)
                metric.user = request.user
                metric.save()
                return redirect(redirect_target)
        elif form_type == "activity":
            activity_form = ActivityForm(request.POST)
            if activity_form.is_valid():
                ActivityEntry.objects.update_or_create(
                    user=request.user,
                    date=activity_form.cleaned_data["date"],
                    defaults={
                        "aerobics": activity_form.cleaned_data["aerobics"],
                        "yoga": activity_form.cleaned_data["yoga"],
                        "meditation": activity_form.cleaned_data["meditation"],
                    },
                )
                return redirect(redirect_target)
        elif form_type == "appointment":
            appointment_form = AppointmentForm(request.POST)
            if appointment_form.is_valid():
                appointment = appointment_form.save(commit=False)
                appointment.user = request.user
                appointment.save()
                return redirect(redirect_target)

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
    activity_series = _activity_series(request.user, selected_month)
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
        "activity_month_label": f"{_month_name_ro(selected_month)} {selected_month.year}",
        "activity_month_value": selected_month_value,
        "activity_month_options": _activity_month_options(selected_month),
        "appointments": appointments,
    }
    return render(request, "pages/dashboard.html", context)

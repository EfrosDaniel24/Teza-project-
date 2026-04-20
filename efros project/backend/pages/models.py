from django.conf import settings
from django.db import models


class Profile(models.Model):
    GENDER_CHOICES = [
        ("masculin", "Masculin"),
        ("feminin", "Feminin"),
        ("altul", "Altul"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    chest_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    waist_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    hips_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    def __str__(self) -> str:
        return f"Profile({self.user})"


class HealthMetric(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="metrics")
    blood_sugar_mg = models.PositiveSmallIntegerField()
    bpm = models.PositiveSmallIntegerField()
    blood_pressure_sys = models.PositiveSmallIntegerField()
    blood_pressure_dia = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Metric({self.user}, {self.created_at:%Y-%m-%d})"


class ActivityEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    date = models.DateField()
    aerobics = models.PositiveSmallIntegerField(default=0)
    yoga = models.PositiveSmallIntegerField(default=0)
    meditation = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["date"]
        unique_together = ("user", "date")

    def __str__(self) -> str:
        return f"Activity({self.user}, {self.date})"


class Appointment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    date = models.DateField()
    title = models.CharField(max_length=140)

    class Meta:
        ordering = ["date"]

    def __str__(self) -> str:
        return f"Appointment({self.user}, {self.date})"


class Goal(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goal")
    target_weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    target_bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    water_goal_ml = models.PositiveSmallIntegerField(default=2000)
    sleep_goal_hours = models.DecimalField(max_digits=3, decimal_places=1, default=8)
    activity_goal_percent = models.PositiveSmallIntegerField(default=60)

    def __str__(self) -> str:
        return f"Goal({self.user})"


class WaterLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="water_logs")
    date = models.DateField()
    amount_ml = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        unique_together = ("user", "date")

    def __str__(self) -> str:
        return f"Water({self.user}, {self.date})"


class SleepLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sleep_logs")
    date = models.DateField()
    hours = models.DecimalField(max_digits=3, decimal_places=1, default=0)

    class Meta:
        ordering = ["-date"]
        unique_together = ("user", "date")

    def __str__(self) -> str:
        return f"Sleep({self.user}, {self.date})"

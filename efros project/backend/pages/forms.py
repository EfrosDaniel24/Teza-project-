from django import forms
from django.contrib.auth import authenticate, get_user_model

from .models import ActivityEntry, Appointment, Goal, HealthMetric, Profile, SleepLog, WaterLog


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "field", "placeholder": "Email"}),
    )
    password = forms.CharField(
        label="Parola",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "field", "placeholder": "Parola"}),
    )
    age = forms.IntegerField(
        label="Vârsta",
        min_value=1,
        max_value=120,
        widget=forms.NumberInput(attrs={"class": "field", "placeholder": "Vârsta"}),
    )
    gender = forms.ChoiceField(
        label="Genul",
        choices=Profile.GENDER_CHOICES,
        widget=forms.Select(attrs={"class": "field"}),
    )
    height_cm = forms.DecimalField(
        label="Înălțime",
        min_value=50,
        max_value=250,
        decimal_places=1,
        max_digits=5,
        widget=forms.NumberInput(attrs={"class": "field", "placeholder": "Înălțime"}),
    )
    weight_kg = forms.DecimalField(
        label="Greutate",
        min_value=20,
        max_value=300,
        decimal_places=1,
        max_digits=5,
        widget=forms.NumberInput(attrs={"class": "field", "placeholder": "Greutate"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        User = get_user_model()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Există deja un cont cu acest email.")
        return email


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "field", "placeholder": "Email"}),
    )
    password = forms.CharField(
        label="Parola",
        widget=forms.PasswordInput(attrs={"class": "field", "placeholder": "Parola"}),
    )

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            user = authenticate(username=email.strip().lower(), password=password)
            if user is None:
                raise forms.ValidationError("Email sau parolă incorectă.")
            cleaned["user"] = user
        return cleaned


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "age",
            "gender",
            "height_cm",
            "weight_kg",
            "chest_cm",
            "waist_cm",
            "hips_cm",
        ]
        widgets = {
            "age": forms.NumberInput(attrs={"class": "panel-input", "placeholder": "Vârsta"}),
            "gender": forms.Select(attrs={"class": "panel-input"}),
            "height_cm": forms.NumberInput(attrs={"class": "panel-input", "placeholder": "Înălțime (cm)"}),
            "weight_kg": forms.NumberInput(attrs={"class": "panel-input", "placeholder": "Greutate (kg)"}),
            "chest_cm": forms.NumberInput(attrs={"class": "panel-input", "placeholder": "Piept (cm)"}),
            "waist_cm": forms.NumberInput(attrs={"class": "panel-input", "placeholder": "Talie (cm)"}),
            "hips_cm": forms.NumberInput(attrs={"class": "panel-input", "placeholder": "Șolduri (cm)"}),
        }


class MetricForm(forms.ModelForm):
    class Meta:
        model = HealthMetric
        fields = ["blood_sugar_mg", "bpm", "blood_pressure_sys", "blood_pressure_dia"]
        widgets = {
            "blood_sugar_mg": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Glucoză (mg/dL)"}),
            "bpm": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "BPM"}),
            "blood_pressure_sys": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "SYS"}),
            "blood_pressure_dia": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "DIA"}),
        }


class ActivityForm(forms.ModelForm):
    class Meta:
        model = ActivityEntry
        fields = ["date", "aerobics", "yoga", "meditation"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "mini-input", "type": "date"}),
            "aerobics": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Aerobics %"}),
            "yoga": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Yoga %"}),
            "meditation": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Meditation %"}),
        }


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["date", "title"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "mini-input", "type": "date"}),
            "title": forms.TextInput(attrs={"class": "mini-input", "placeholder": "Titlu programare"}),
        }


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["target_weight_kg", "target_bmi", "water_goal_ml", "sleep_goal_hours", "activity_goal_percent"]
        widgets = {
            "target_weight_kg": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Greutate țintă"}),
            "target_bmi": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "BMI țintă"}),
            "water_goal_ml": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Apă/zi (ml)"}),
            "sleep_goal_hours": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Somn (ore)"}),
            "activity_goal_percent": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Activitate %"}),
        }


class WaterLogForm(forms.ModelForm):
    class Meta:
        model = WaterLog
        fields = ["date", "amount_ml"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "mini-input", "type": "date"}),
            "amount_ml": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Apă băută (ml)"}),
        }


class SleepLogForm(forms.ModelForm):
    class Meta:
        model = SleepLog
        fields = ["date", "hours"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "mini-input", "type": "date"}),
            "hours": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Ore de somn"}),
        }

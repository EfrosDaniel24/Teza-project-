from django import forms
from django.contrib.auth import authenticate, get_user_model

from .models import ActivityEntry, Appointment, FoodEntry, Goal, HealthMetric, Profile, SleepLog, WaterLog


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
            "blood_sugar_mg": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Glucoză (mg/dL)", "min": 40, "max": 600}),
            "bpm": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "BPM", "min": 30, "max": 240}),
            "blood_pressure_sys": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "SYS", "min": 70, "max": 260}),
            "blood_pressure_dia": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "DIA", "min": 40, "max": 160}),
        }

    def clean_blood_sugar_mg(self):
        value = self.cleaned_data["blood_sugar_mg"]
        if not 40 <= value <= 600:
            raise forms.ValidationError("Glucoza trebuie să fie între 40 și 600 mg/dL.")
        return value

    def clean_bpm(self):
        value = self.cleaned_data["bpm"]
        if not 30 <= value <= 240:
            raise forms.ValidationError("BPM trebuie să fie între 30 și 240.")
        return value

    def clean_blood_pressure_sys(self):
        value = self.cleaned_data["blood_pressure_sys"]
        if not 70 <= value <= 260:
            raise forms.ValidationError("SYS trebuie să fie între 70 și 260.")
        return value

    def clean_blood_pressure_dia(self):
        value = self.cleaned_data["blood_pressure_dia"]
        if not 40 <= value <= 160:
            raise forms.ValidationError("DIA trebuie să fie între 40 și 160.")
        return value


class ActivityForm(forms.ModelForm):
    class Meta:
        model = ActivityEntry
        fields = ["date", "aerobics", "yoga", "meditation"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "mini-input", "type": "date"}),
            "aerobics": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Aerobics %", "min": 0, "max": 100}),
            "yoga": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Yoga %", "min": 0, "max": 100}),
            "meditation": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Meditation %", "min": 0, "max": 100}),
        }

    def clean(self):
        cleaned = super().clean()
        for key in ("aerobics", "yoga", "meditation"):
            value = cleaned.get(key)
            if value is not None and not 0 <= value <= 100:
                self.add_error(key, "Valoarea trebuie să fie între 0 și 100.")
        return cleaned


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
            "water_goal_ml": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Apă/zi (ml)", "min": 500, "max": 7000}),
            "sleep_goal_hours": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Somn (ore)", "min": 1, "max": 24}),
            "activity_goal_percent": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Activitate %", "min": 0, "max": 100}),
        }

    def clean_activity_goal_percent(self):
        value = self.cleaned_data["activity_goal_percent"]
        if not 0 <= value <= 100:
            raise forms.ValidationError("Obiectivul de activitate trebuie să fie între 0 și 100.")
        return value


class WaterLogForm(forms.ModelForm):
    class Meta:
        model = WaterLog
        fields = ["date", "amount_ml"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "mini-input", "type": "date"}),
            "amount_ml": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Apă băută (ml)", "min": 0, "max": 7000}),
        }

    def clean_amount_ml(self):
        value = self.cleaned_data["amount_ml"]
        if not 0 <= value <= 7000:
            raise forms.ValidationError("Cantitatea de apă trebuie să fie între 0 și 7000 ml.")
        return value


class SleepLogForm(forms.ModelForm):
    class Meta:
        model = SleepLog
        fields = ["date", "hours"]
        widgets = {
            "date": forms.DateInput(attrs={"class": "mini-input", "type": "date"}),
            "hours": forms.NumberInput(attrs={"class": "mini-input", "placeholder": "Ore de somn", "min": 0, "max": 24, "step": 0.1}),
        }

    def clean_hours(self):
        value = self.cleaned_data["hours"]
        if not 0 <= value <= 24:
            raise forms.ValidationError("Orele de somn trebuie să fie între 0 și 24.")
        return value


class FoodEntryForm(forms.ModelForm):
    class Meta:
        model = FoodEntry
        fields = ["meal_type", "name", "serving", "calories", "protein_g", "carbs_g", "fat_g"]
        widgets = {
            "meal_type": forms.HiddenInput(),
            "name": forms.TextInput(attrs={"class": "food-input", "placeholder": "Nume aliment"}),
            "serving": forms.TextInput(attrs={"class": "food-input", "placeholder": "Portie"}),
            "calories": forms.NumberInput(attrs={"class": "food-input", "placeholder": "kcal", "min": 0}),
            "protein_g": forms.NumberInput(attrs={"class": "food-input", "placeholder": "Proteine (g)", "min": 0}),
            "carbs_g": forms.NumberInput(attrs={"class": "food-input", "placeholder": "Carbohidrati (g)", "min": 0}),
            "fat_g": forms.NumberInput(attrs={"class": "food-input", "placeholder": "Grasimi (g)", "min": 0}),
        }

    def clean_calories(self):
        value = self.cleaned_data["calories"]
        if value < 0:
            raise forms.ValidationError("Caloriile nu pot fi negative.")
        return value

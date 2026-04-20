from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ActivityEntry, Appointment, FoodEntry, Goal, Profile, SleepLog, WaterLog


class AppFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester@example.com",
            email="tester@example.com",
            password="safe-pass-123",
        )
        Profile.objects.create(user=self.user, age=25, gender="masculin", height_cm=180, weight_kg=80)

    def login(self):
        self.client.login(username="tester@example.com", password="safe-pass-123")

    def test_public_pages_load(self):
        for name in ("landing", "about", "howto", "login", "register"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

    def test_private_pages_require_auth(self):
        for name in ("dashboard", "nutrition", "profile", "goals", "habits", "history"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse("login"), response.url)

    def test_dashboard_activity_is_updated_not_duplicated(self):
        self.login()
        today = timezone.localdate()
        payload = {
            "form_type": "activity",
            "date": today.isoformat(),
            "aerobics": 20,
            "yoga": 30,
            "meditation": 40,
        }
        self.client.post(reverse("dashboard"), data=payload)
        payload["aerobics"] = 50
        self.client.post(reverse("dashboard"), data=payload)
        entries = ActivityEntry.objects.filter(user=self.user, date=today)
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().aerobics, 50)

    def test_nutrition_add_and_delete_food(self):
        self.login()
        today = timezone.localdate().isoformat()
        add_payload = {
            "action": "add_food",
            "date": today,
            "meal_type": "breakfast",
            "name": "Ovăz",
            "serving": "80g",
            "calories": 310,
            "protein_g": "10.5",
            "carbs_g": "52.0",
            "fat_g": "5.2",
        }
        self.client.post(reverse("nutrition"), data=add_payload)
        entry = FoodEntry.objects.get(user=self.user)
        self.assertEqual(entry.name, "Ovăz")

        delete_payload = {"action": "delete_food", "entry_id": entry.id, "date": today}
        self.client.post(reverse("nutrition"), data=delete_payload)
        self.assertFalse(FoodEntry.objects.filter(id=entry.id).exists())

    def test_goals_save(self):
        self.login()
        payload = {
            "target_weight_kg": "74.0",
            "target_bmi": "23.0",
            "water_goal_ml": 2600,
            "sleep_goal_hours": "7.5",
            "activity_goal_percent": 70,
        }
        self.client.post(reverse("goals"), data=payload)
        goal = Goal.objects.get(user=self.user)
        self.assertEqual(goal.water_goal_ml, 2600)
        self.assertEqual(goal.sleep_goal_hours, Decimal("7.5"))

    def test_habits_water_sleep_upsert(self):
        self.login()
        today = timezone.localdate().isoformat()
        self.client.post(reverse("habits"), data={"form_type": "water", "date": today, "amount_ml": 1800})
        self.client.post(reverse("habits"), data={"form_type": "water", "date": today, "amount_ml": 2000})
        self.assertEqual(WaterLog.objects.filter(user=self.user).count(), 1)
        self.assertEqual(WaterLog.objects.get(user=self.user).amount_ml, 2000)

        self.client.post(reverse("habits"), data={"form_type": "sleep", "date": today, "hours": "7.0"})
        self.assertEqual(SleepLog.objects.filter(user=self.user).count(), 1)

    def test_history_add_and_delete_appointment(self):
        self.login()
        today = timezone.localdate().isoformat()
        self.client.post(
            reverse("history"),
            data={"action": "add_appointment", "date": today, "title": "Control anual"},
        )
        item = Appointment.objects.get(user=self.user)
        self.assertEqual(item.title, "Control anual")

        self.client.post(reverse("history"), data={"action": "delete_appointment", "appointment_id": item.id})
        self.assertFalse(Appointment.objects.filter(id=item.id).exists())

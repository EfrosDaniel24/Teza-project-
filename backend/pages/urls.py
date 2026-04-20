from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("about/", views.about, name="about"),
    path("how-to-use/", views.how_to_use, name="howto"),
    path("nutrition/", views.nutrition, name="nutrition"),
    path("profile/", views.profile_page, name="profile"),
    path("goals/", views.goals_page, name="goals"),
    path("habits/", views.habits_page, name="habits"),
    path("history/", views.history_page, name="history"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("about/", views.about, name="about"),
    path("how-to-use/", views.how_to_use, name="howto"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
]

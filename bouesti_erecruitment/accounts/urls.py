from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.RoleAwareLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="recruitment:home"), name="logout"),
    path("profile/", views.profile_view, name="profile"),
]

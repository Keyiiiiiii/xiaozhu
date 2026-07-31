from django.urls import path

from api import auth_views

urlpatterns = [
    path("login/", auth_views.login_view, name="auth_login"),
    path("me/", auth_views.me_view, name="auth_me"),
    path("refresh/", auth_views.refresh_view, name="auth_refresh"),
    path("logout/", auth_views.logout_view, name="auth_logout"),
]

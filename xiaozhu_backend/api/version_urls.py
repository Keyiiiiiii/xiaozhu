from django.urls import path

from api import version_views

urlpatterns = [
    path("check/", version_views.check_update_view, name="version_check"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("", views.knowledge_api, name="knowledge_api"),
]
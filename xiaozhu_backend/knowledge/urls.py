from django.urls import path
from . import views

urlpatterns = [
    path("", views.knowledge_api, name="knowledge_api"),
    path("upload/", views.upload_knowledge_file, name="upload_knowledge_file"),
]

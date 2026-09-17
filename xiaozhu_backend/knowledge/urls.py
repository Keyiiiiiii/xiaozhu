from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.knowledge_api, name="knowledge_api"),
    re_path(r"^$", views.knowledge_api, name="knowledge_api_no_slash"),
    path("upload/", views.upload_knowledge_file, name="upload_knowledge_file"),
    path("download/<int:file_id>/", views.download_file, name="download_file"),
]

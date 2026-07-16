from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_file, name="upload_file"),
    path("speech-to-text/", views.speech_to_text, name="speech_to_text"),
]

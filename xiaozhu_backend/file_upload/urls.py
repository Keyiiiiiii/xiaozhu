from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_file, name="upload_file"),
    path("speech-to-text/", views.speech_to_text, name="speech_to_text"),
    path("summarize/", views.summarize_record, name="summarize_record"),
    path("extract-todos/", views.extract_todos, name="extract_todos"),
    path("record-ids/", views.get_record_ids, name="get_record_ids"),
    path("record-detail/", views.get_record_detail, name="get_record_detail"),
    path("update-original-text/", views.update_original_text, name="update_original_text"),
    path("delete-record/", views.delete_record, name="delete_record"),
    path("get-audio-file/", views.get_audio_file, name="get_audio_file"),
]

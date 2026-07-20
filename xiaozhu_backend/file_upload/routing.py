from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/asr/(?P<job_id>\w+)/$", consumers.ASRConsumer.as_asgi()),
]

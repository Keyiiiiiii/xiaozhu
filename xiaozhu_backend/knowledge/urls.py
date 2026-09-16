from django.urls import path, re_path
from . import views

urlpatterns = [
    # 知识库问答
    path("", views.knowledge_api, name="knowledge_api"),
    re_path(r"^$", views.knowledge_api, name="knowledge_api_no_slash"),
    path("upload/", views.upload_knowledge_file, name="upload_knowledge_file"),
    path("download/<int:file_id>/", views.download_file, name="download_file"),

    # 工单系统
    path("tickets/", views.ticket_list, name="ticket_list"),          # GET 列表
    path("tickets/create/", views.ticket_create, name="ticket_create"),  # POST 创建
    path("tickets/<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:ticket_id>/answer/", views.ticket_answer, name="ticket_answer"),
    path("tickets/<int:ticket_id>/close/", views.ticket_close, name="ticket_close"),
    path("tickets/<int:ticket_id>/upload/", views.ticket_upload, name="ticket_upload"),
]

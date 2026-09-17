import uuid
import os
from django.db import models
from django.conf import settings


class KnowledgeFile(models.Model):
    file_name = models.CharField(
        max_length=255,
        verbose_name="文件名"
    )
    file_url = models.URLField(
        max_length=500,
        verbose_name="文件URL"
    )
    file_size = models.IntegerField(
        verbose_name="文件大小(字节)"
    )
    file_type = models.CharField(
        max_length=100,
        verbose_name="文件类型"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="上传时间"
    )

    class Meta:
        verbose_name = "知识库文件"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.file_name

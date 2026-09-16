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


# =====================================================================
# 工单系统（问题上报 → 产品经理解答 → 知识库闭环）
# =====================================================================

class Ticket(models.Model):
    """
    问题上报工单。

    流程：
      客户经理前端点"问题上报" → 创建 Ticket（status=pending）
      → 产品经理查看未处理工单 → 填写 manager_answer（status=processing→resolved）
      → 经理关联 KnowledgeFile 或上传新文件到知识库（status=closed）
      → 保障人收到 Notification 通知
    """

    STATUS_CHOICES = [
        ("pending", "待处理"),       # 刚创建，还没人接手
        ("processing", "处理中"),     # 产品经理已接手，正在解答
        ("resolved", "已解决"),       # 产品经理已给出回答，等确认
        ("closed", "已闭环"),         # 已关联知识库条目，彻底关闭
        ("rejected", "已驳回"),       # 非有效问题/重复问题
    ]

    # 核心内容
    question = models.TextField(
        verbose_name="用户原始问题"
    )
    agent_answer = models.TextField(
        null=True,
        blank=True,
        verbose_name="智能体当时给出的回答（便于经理理解上下文）"
    )
    reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="用户认为没解决的原因/补充描述"
    )

    # 产品经理的解答
    manager_answer = models.TextField(
        null=True,
        blank=True,
        verbose_name="产品经理的正式回答"
    )
    manager_note = models.TextField(
        null=True,
        blank=True,
        verbose_name="经理内部备注（不对用户可见）"
    )

    # 关联：解决后关联到知识库条目
    related_file = models.ForeignKey(
        KnowledgeFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="关联的知识库文件（闭环时填写）"
    )
    related_file_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="关联的知识库文件名快照（冗余字段，便于列表展示）"
    )

    # 用户/经理/保障人
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reported_tickets",
        verbose_name="上报人（客户经理）"
    )
    handler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_tickets",
        verbose_name="处理人（产品经理）"
    )

    # 状态流转
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="工单状态"
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="经理给出解答的时间"
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="工单闭环时间"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间"
    )

    class Meta:
        verbose_name = "工单"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["reporter", "status"]),
            models.Index(fields=["handler", "status"]),
        ]

    def __str__(self):
        return f"#{self.id} {self.question[:40]} ({self.get_status_display()})"


class TicketFile(models.Model):
    """
    工单附件（截图、需求文档等）。
    文件通过现有 upload_knowledge_file 接口上传到 MinIO 后，
    这里只存 URL 关联。
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="所属工单"
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name="文件名"
    )
    file_url = models.URLField(
        max_length=500,
        verbose_name="文件URL"
    )
    file_size = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="文件大小(字节)"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="上传人"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="上传时间"
    )

    class Meta:
        verbose_name = "工单附件"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.file_name} (Ticket #{self.ticket_id})"

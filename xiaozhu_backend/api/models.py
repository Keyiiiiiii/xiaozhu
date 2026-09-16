# api/models.py
"""
Models definition for RongXiaoZhu backend service.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


# =====================================================================
# 1. User (用户表)
# =====================================================================
class User(AbstractUser):
    """
    User model containing work ID, name, role ID, and organization.
    """
    work_id = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="工号"
    )
    name = models.CharField(
        max_length=100, 
        verbose_name="姓名"
    )
    role_id = models.CharField(
        max_length=50, 
        verbose_name="角色ID"
    )
    organization = models.CharField(
        max_length=150, 
        verbose_name="所属机构"
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name


# =====================================================================
# 2. VisitRecord (走访记录表)
# =====================================================================
class VisitRecord(models.Model):
    """
    Walk-visit records containing customer info, audio URL, text transcriptions,
    and associated business types.
    """
    STATUS_CHOICES = [
        ("pending", "等待处理"),
        ("processing", "处理中"),
        ("success", "处理成功"),
        ("failed", "处理失败"),
    ]

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE, 
        verbose_name="创建人"
    )
    customer_name = models.CharField(
        max_length=150, 
        verbose_name="走访对象"
    )
    audio_url = models.URLField(
        max_length=500, 
        null=True, 
        blank=True,
        verbose_name="音频文件URL"
    )
    original_text = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="原始转写文本"
    )
    ai_summary = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="AI总结文本"
    )
    visit_time = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="走访时间"
    )
    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="沟通时长"
    )
    business_type = models.CharField(
        null=True, 
        blank=True,
        max_length=100, 
        verbose_name="关联业务类型"
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending",
        verbose_name="处理状态"
    )

    class Meta:
        verbose_name = "走访记录"
        verbose_name_plural = verbose_name


# =====================================================================
# 3. TodoItem (待办事项表)
# =====================================================================
class TodoItem(models.Model):
    """
    To-do items with trigger options and state closing loop.
    """
    STATUS_CHOICES = [
        ("pending", "未办"),
        ("ongoing", "进行中"),
        ("closed", "闭环"),
    ]

    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="负责人"
    )
    visit_record = models.ForeignKey(
        VisitRecord, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="关联走访记录"
    )
    content = models.TextField(
        verbose_name="事项内容"
    )
    trigger_type = models.CharField(
        max_length=50, 
        verbose_name="触发类型"
    )
    trigger_value = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name="触发阈值"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending",
        verbose_name="状态"
    )

    class Meta:
        verbose_name = "待办事项"
        verbose_name_plural = verbose_name


# =====================================================================
# 4. Notification (通知分发表)
# =====================================================================
class Notification(models.Model):
    """
    Notification broadcast records categorized by levels and targets.
    """
    STATUS_CHOICES = [
        ("unread", "未读"),
        ("read", "已读"),
    ]
    title = models.CharField(
        max_length=250, 
        verbose_name="标题"
    )
    content = models.TextField(
        verbose_name="内容"
    )
    level = models.CharField(
        max_length=50, 
        verbose_name="发送层级"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE, 
        verbose_name="发送人"
    )
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES,
        default="unread",
        verbose_name="状态"
    )

    # [暂不启用] MVP阶段不包含审批流
    # approval_id = models.CharField(max_length=150, blank=True, verbose_name="关联审批工单ID")

    class Meta:
        verbose_name = "通知分发"
        verbose_name_plural = verbose_name


# =====================================================================
# 5. QuotaRule (通知额度规则表)
# =====================================================================
class QuotaRule(models.Model):
    """
    Monthly configurations for notification quotas and thresholds.
    """
    level = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="配置层级/专项"
    )
    monthly_quota = models.IntegerField(
        verbose_name="月度推送配额"
    )

    class Meta:
        verbose_name = "通知额度规则"
        verbose_name_plural = verbose_name


# =====================================================================
# 6. AppVersion (应用版本表)
# =====================================================================
class AppVersion(models.Model):
    """
    Mobile application version configurations supporting forced updates.

    更新类型 update_type 与概要设计文档保持一致：
      0: 提示热更 (WGT 资源包，可取消)
      1: 强制热更 (WGT 资源包，不可取消)
      2: 提示整包 (APK/IPA，可取消)
      3: 强制整包 (APK/IPA，不可取消)
    """
    PLATFORM_CHOICES = [
        ("Android", "Android"),
        ("iOS", "iOS"),
    ]
    UPDATE_TYPE_CHOICES = [
        (0, "提示热更"),
        (1, "强制热更"),
        (2, "提示整包"),
        (3, "强制整包"),
    ]

    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        verbose_name="平台类型",
    )
    version = models.CharField(
        max_length=50,
        verbose_name="版本号",
    )
    version_code = models.IntegerField(
        verbose_name="构建号",
    )
    update_type = models.IntegerField(
        choices=UPDATE_TYPE_CHOICES,
        default=0,
        verbose_name="更新类型",
    )
    download_url = models.URLField(
        max_length=500,
        verbose_name="下载包URL",
    )
    changelog = models.TextField(
        blank=True,
        default="",
        verbose_name="更新日志说明",
    )
    is_silent = models.BooleanField(
        default=False,
        verbose_name="是否静默更新",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否启用",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )

    class Meta:
        verbose_name = "应用版本"
        verbose_name_plural = verbose_name
        ordering = ["-version_code", "-created_at"]
        indexes = [
            models.Index(fields=["platform", "is_active"]),
        ]
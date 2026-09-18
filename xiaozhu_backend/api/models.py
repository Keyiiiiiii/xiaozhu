# api/models.py
"""
Models definition for RongXiaoZhu backend service.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone


# =====================================================================
# 1. Permission / Role (权限点与角色)
# =====================================================================
class Permission(models.Model):
    """
    Feature-level permission codes used for authorization across the app.
    """
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="权限编码",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="权限名称",
    )

    class Meta:
        verbose_name = "权限点"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} ({self.code})"


class Role(models.Model):
    """
    Personnel levels (frontline / district / city) bound to permission codes.
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="角色编码",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="角色名称",
    )
    level = models.PositiveSmallIntegerField(
        verbose_name="层级",
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="roles",
        verbose_name="权限点",
    )

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = verbose_name
        ordering = ["level"]

    def __str__(self):
        return self.name


# =====================================================================
# 2. Organization / User (组织与用户)
# =====================================================================
class Department(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="部门编码")
    name = models.CharField(max_length=100, verbose_name="部门名称")

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = verbose_name
        ordering = ["code"]

    def __str__(self):
        return self.name


class District(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="区县编码")
    name = models.CharField(max_length=100, verbose_name="区县名称")

    class Meta:
        verbose_name = "区县"
        verbose_name_plural = verbose_name
        ordering = ["code"]

    def __str__(self):
        return self.name


class Grid(models.Model):
    code = models.CharField(max_length=50, verbose_name="网格编码")
    name = models.CharField(max_length=100, verbose_name="网格名称")
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="grids",
        verbose_name="所属区县",
    )

    class Meta:
        verbose_name = "网格"
        verbose_name_plural = verbose_name
        ordering = ["district_id", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["district", "code"],
                name="uniq_grid_code_per_district",
            ),
        ]

    def __str__(self):
        return f"{self.district.name} / {self.name}"


class User(AbstractUser):
    """
    User model containing work ID, name, role, and organization text.
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
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="角色",
    )
    organization = models.CharField(
        max_length=150, 
        verbose_name="所属机构"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="所属部门",
    )
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="所属区县",
    )
    grid = models.ForeignKey(
        Grid,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="所属网格",
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def clean(self):
        super().clean()
        errors = {}
        role_code = self.role.code if self.role_id else None

        if role_code == "district" and not self.district_id:
            errors["district"] = "区县专项用户必须关联区县。"
        if role_code == "frontline":
            if not self.district_id:
                errors["district"] = "一线用户必须关联区县。"
            if not self.grid_id:
                errors["grid"] = "一线用户必须关联网格。"
        if self.grid_id and self.district_id:
            if self.grid.district_id != self.district_id:
                errors["grid"] = "用户所属网格必须位于用户所属区县。"

        if errors:
            raise ValidationError(errors)


# =====================================================================
# 3. VisitRecord (走访记录表)
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
# 4. TodoItem (待办事项表)
# =====================================================================
class TodoItem(models.Model):
    """
    To-do events with priority and closed-loop status.
    """
    STATUS_CHOICES = [
        ("pending", "未办"),
        ("ongoing", "进行中"),
        ("closed", "已闭环"),
    ]
    PRIORITY_CHOICES = [
        ("normal", "常规"),
        ("high", "高优"),
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
    title = models.CharField(
        max_length=250,
        default="",
        verbose_name="标题",
    )
    event_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="日期",
    )
    event_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="时间",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="normal",
        verbose_name="优先级",
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending",
        verbose_name="状态"
    )
    is_ai_generated = models.BooleanField(
        default=False,
        verbose_name="是否AI生成",
    )

    class Meta:
        verbose_name = "待办事项"
        verbose_name_plural = verbose_name


# =====================================================================
# 5. Notification (通知分发表)
# =====================================================================
class Notification(models.Model):
    """
    Notification broadcast records categorized by levels and targets.
    """
    LEVEL_CHOICES = [
        ("normal", "普通"),
        ("important", "重要"),
        ("urgent", "紧急"),
    ]
    SCOPE_CHOICES = [
        ("city", "全市"),
        ("district", "区县"),
        ("grid", "网格"),
    ]
    STATUS_CHOICES = [
        ("published", "已发布"),
        ("revoked", "已撤回"),
    ]
    title = models.CharField(
        max_length=250, 
        verbose_name="标题"
    )
    content = models.TextField(
        verbose_name="内容"
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="normal",
        verbose_name="紧急程度",
    )
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default="city",
        verbose_name="下发范围",
    )
    target_district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="targeted_notifications",
        verbose_name="目标区县",
    )
    target_grid = models.ForeignKey(
        Grid,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="targeted_notifications",
        verbose_name="目标网格",
    )
    publisher = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="published_notifications",
        verbose_name="发送人"
    )
    force_display = models.BooleanField(default=False, verbose_name="是否强制开屏")
    force_duration = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="强制展示秒数",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="published",
        verbose_name="发布状态",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    published_at = models.DateTimeField(default=timezone.now, verbose_name="发布时间")
    expire_at = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name="撤回时间")

    class Meta:
        verbose_name = "通知分发"
        verbose_name_plural = verbose_name
        ordering = ["-published_at", "-id"]
        indexes = [
            models.Index(
                fields=["status", "expire_at", "published_at"],
                name="notif_status_exp_pub_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        scope="city",
                        target_district__isnull=True,
                        target_grid__isnull=True,
                    )
                    | models.Q(
                        scope="district",
                        target_district__isnull=False,
                        target_grid__isnull=True,
                    )
                    | models.Q(
                        scope="grid",
                        target_district__isnull=False,
                        target_grid__isnull=False,
                    )
                ),
                name="notif_scope_targets_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(level="normal", force_display=False, force_duration=0)
                    | models.Q(level="important", force_display=True, force_duration=3)
                    | models.Q(level="urgent", force_display=True, force_duration=10)
                ),
                name="notif_force_rule_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(expire_at__isnull=True)
                    | models.Q(expire_at__gt=models.F("published_at"))
                ),
                name="notif_expiry_after_publish",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="published", revoked_at__isnull=True)
                    | models.Q(status="revoked", revoked_at__isnull=False)
                ),
                name="notif_status_timestamp_valid",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.scope == "city":
            if self.target_district_id or self.target_grid_id:
                errors["scope"] = "全市通知不能指定目标区县或网格。"
        elif self.scope == "district":
            if not self.target_district_id or self.target_grid_id:
                errors["scope"] = "区县通知必须且只能指定目标区县。"
        elif self.scope == "grid":
            if not self.target_district_id or not self.target_grid_id:
                errors["scope"] = "网格通知必须指定目标区县和网格。"
            elif self.target_grid.district_id != self.target_district_id:
                errors["target_grid"] = "目标网格必须属于目标区县。"

        force_rules = {
            "normal": (False, 0),
            "important": (True, 3),
            "urgent": (True, 10),
        }
        expected = force_rules.get(self.level)
        if expected and (self.force_display, self.force_duration) != expected:
            errors["force_duration"] = "强制展示配置与通知级别不一致。"
        if self.expire_at and self.published_at and self.expire_at <= self.published_at:
            errors["expire_at"] = "过期时间必须晚于发布时间。"

        if errors:
            raise ValidationError(errors)


# =====================================================================
# 6. NotificationReceiver (通知接收记录)
# =====================================================================
class NotificationReceiver(models.Model):
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="receivers",
        verbose_name="通知",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="received_notifications",
        verbose_name="接收人",
    )
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="阅读时间")
    force_ack_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="强制展示确认时间",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="接收时间")

    class Meta:
        verbose_name = "通知接收记录"
        verbose_name_plural = verbose_name
        constraints = [
            models.UniqueConstraint(
                fields=["notification", "user"],
                name="uniq_notification_receiver",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "read_at"], name="recv_user_read_idx"),
            models.Index(
                fields=["user", "force_ack_at"],
                name="recv_user_force_idx",
            ),
        ]


# =====================================================================
# 7. QuotaRule (通知额度规则表)
# =====================================================================
class QuotaRule(models.Model):
    """
    Monthly configurations for notification quotas and thresholds.
    """
    level = models.OneToOneField(
        Role,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="quota_rule",
        verbose_name="配置层级",
    )
    monthly_quota = models.IntegerField(
        verbose_name="月度推送配额"
    )

    class Meta:
        verbose_name = "通知额度规则"
        verbose_name_plural = verbose_name


# =====================================================================
# 8. AppVersion (应用版本表)
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
            models.Index(
                fields=["platform", "is_active"],
                name="appver_platform_active_idx",
            ),
        ]
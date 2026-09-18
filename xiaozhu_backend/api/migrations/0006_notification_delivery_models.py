import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def revoke_legacy_notifications(apps, schema_editor):
    Notification = apps.get_model("api", "Notification")
    Notification.objects.all().update(
        status="revoked",
        revoked_at=django.utils.timezone.now(),
    )


def restore_legacy_notification_status(apps, schema_editor):
    Notification = apps.get_model("api", "Notification")
    Notification.objects.all().update(status="unread", revoked_at=None)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_organization_models"),
    ]

    operations = [
        migrations.RenameField(
            model_name="notification",
            old_name="sender",
            new_name="publisher",
        ),
        migrations.AlterField(
            model_name="notification",
            name="publisher",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="published_notifications",
                to=settings.AUTH_USER_MODEL,
                verbose_name="发送人",
            ),
        ),
        migrations.RemoveField(
            model_name="notification",
            name="level",
        ),
        migrations.AddField(
            model_name="notification",
            name="level",
            field=models.CharField(
                choices=[
                    ("normal", "普通"),
                    ("important", "重要"),
                    ("urgent", "紧急"),
                ],
                default="normal",
                max_length=20,
                verbose_name="紧急程度",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="scope",
            field=models.CharField(
                choices=[
                    ("city", "全市"),
                    ("district", "区县"),
                    ("grid", "网格"),
                ],
                default="city",
                max_length=20,
                verbose_name="下发范围",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="target_district",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="targeted_notifications",
                to="api.district",
                verbose_name="目标区县",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="target_grid",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="targeted_notifications",
                to="api.grid",
                verbose_name="目标网格",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="force_display",
            field=models.BooleanField(default=False, verbose_name="是否强制开屏"),
        ),
        migrations.AddField(
            model_name="notification",
            name="force_duration",
            field=models.PositiveSmallIntegerField(
                default=0,
                verbose_name="强制展示秒数",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="创建时间",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="notification",
            name="published_at",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                verbose_name="发布时间",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="expire_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="过期时间",
            ),
        ),
        migrations.AddField(
            model_name="notification",
            name="revoked_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="撤回时间",
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="status",
            field=models.CharField(
                choices=[("published", "已发布"), ("revoked", "已撤回")],
                default="published",
                max_length=20,
                verbose_name="发布状态",
            ),
        ),
        migrations.RunPython(
            revoke_legacy_notifications,
            restore_legacy_notification_status,
        ),
        migrations.CreateModel(
            name="NotificationReceiver",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "read_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="阅读时间"),
                ),
                (
                    "force_ack_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="强制展示确认时间",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="接收时间"),
                ),
                (
                    "notification",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="receivers",
                        to="api.notification",
                        verbose_name="通知",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="received_notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="接收人",
                    ),
                ),
            ],
            options={
                "verbose_name": "通知接收记录",
                "verbose_name_plural": "通知接收记录",
            },
        ),
        migrations.AlterModelOptions(
            name="notification",
            options={
                "ordering": ["-published_at", "-id"],
                "verbose_name": "通知分发",
                "verbose_name_plural": "通知分发",
            },
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["status", "expire_at", "published_at"],
                name="notif_status_exp_pub_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
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
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(level="normal", force_display=False, force_duration=0)
                    | models.Q(level="important", force_display=True, force_duration=3)
                    | models.Q(level="urgent", force_display=True, force_duration=10)
                ),
                name="notif_force_rule_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(expire_at__isnull=True)
                    | models.Q(expire_at__gt=models.F("published_at"))
                ),
                name="notif_expiry_after_publish",
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(status="published", revoked_at__isnull=True)
                    | models.Q(status="revoked", revoked_at__isnull=False)
                ),
                name="notif_status_timestamp_valid",
            ),
        ),
        migrations.AddIndex(
            model_name="notificationreceiver",
            index=models.Index(
                fields=["user", "read_at"],
                name="recv_user_read_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notificationreceiver",
            index=models.Index(
                fields=["user", "force_ack_at"],
                name="recv_user_force_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="notificationreceiver",
            constraint=models.UniqueConstraint(
                fields=("notification", "user"),
                name="uniq_notification_receiver",
            ),
        ),
    ]

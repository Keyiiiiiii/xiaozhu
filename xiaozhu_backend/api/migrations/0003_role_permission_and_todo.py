import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_visitrecord_duration_seconds"),
    ]

    operations = [
        migrations.CreateModel(
            name="Permission",
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
                    "code",
                    models.CharField(max_length=100, unique=True, verbose_name="权限编码"),
                ),
                ("name", models.CharField(max_length=100, verbose_name="权限名称")),
            ],
            options={
                "verbose_name": "权限点",
                "verbose_name_plural": "权限点",
            },
        ),
        migrations.CreateModel(
            name="Role",
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
                    "code",
                    models.CharField(max_length=50, unique=True, verbose_name="角色编码"),
                ),
                ("name", models.CharField(max_length=100, verbose_name="角色名称")),
                ("level", models.PositiveSmallIntegerField(verbose_name="层级")),
                (
                    "permissions",
                    models.ManyToManyField(
                        blank=True,
                        related_name="roles",
                        to="api.permission",
                        verbose_name="权限点",
                    ),
                ),
            ],
            options={
                "verbose_name": "角色",
                "verbose_name_plural": "角色",
                "ordering": ["level"],
            },
        ),
        migrations.RemoveField(
            model_name="user",
            name="role_id",
        ),
        migrations.AddField(
            model_name="user",
            name="role",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="users",
                to="api.role",
                verbose_name="角色",
            ),
        ),
        migrations.RemoveField(
            model_name="todoitem",
            name="content",
        ),
        migrations.RemoveField(
            model_name="todoitem",
            name="trigger_type",
        ),
        migrations.RemoveField(
            model_name="todoitem",
            name="trigger_value",
        ),
        migrations.AddField(
            model_name="todoitem",
            name="title",
            field=models.CharField(default="", max_length=250, verbose_name="标题"),
        ),
        migrations.AddField(
            model_name="todoitem",
            name="event_date",
            field=models.DateField(blank=True, null=True, verbose_name="日期"),
        ),
        migrations.AddField(
            model_name="todoitem",
            name="event_time",
            field=models.TimeField(blank=True, null=True, verbose_name="时间"),
        ),
        migrations.AddField(
            model_name="todoitem",
            name="priority",
            field=models.CharField(
                choices=[("normal", "常规"), ("high", "高优")],
                default="normal",
                max_length=20,
                verbose_name="优先级",
            ),
        ),
        migrations.AddField(
            model_name="todoitem",
            name="is_ai_generated",
            field=models.BooleanField(default=False, verbose_name="是否AI生成"),
        ),
        migrations.AlterField(
            model_name="todoitem",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "未办"),
                    ("ongoing", "进行中"),
                    ("closed", "已闭环"),
                ],
                default="pending",
                max_length=20,
                verbose_name="状态",
            ),
        ),
        migrations.RemoveField(
            model_name="notification",
            name="level",
        ),
        migrations.AddField(
            model_name="notification",
            name="level",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="notifications",
                to="api.role",
                verbose_name="发送层级",
            ),
        ),
        migrations.RemoveField(
            model_name="quotarule",
            name="level",
        ),
        migrations.AddField(
            model_name="quotarule",
            name="level",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="quota_rule",
                to="api.role",
                verbose_name="配置层级",
            ),
        ),
    ]

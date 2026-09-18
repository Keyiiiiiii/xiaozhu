from django.db import migrations, models
import django.utils.timezone


def map_legacy_force_flag(apps, schema_editor):
    AppVersion = apps.get_model("api", "AppVersion")
    AppVersion.objects.filter(is_forced=True).update(update_type=3)
    AppVersion.objects.filter(is_forced=False).update(update_type=2)


def restore_legacy_force_flag(apps, schema_editor):
    AppVersion = apps.get_model("api", "AppVersion")
    AppVersion.objects.filter(update_type__in=[1, 3]).update(is_forced=True)
    AppVersion.objects.exclude(update_type__in=[1, 3]).update(is_forced=False)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_role_permission_and_todo"),
    ]

    operations = [
        migrations.AddField(
            model_name="appversion",
            name="version_code",
            field=models.IntegerField(default=0, verbose_name="构建号"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="appversion",
            name="update_type",
            field=models.IntegerField(
                choices=[
                    (0, "提示热更"),
                    (1, "强制热更"),
                    (2, "提示整包"),
                    (3, "强制整包"),
                ],
                default=2,
                verbose_name="更新类型",
            ),
        ),
        migrations.AddField(
            model_name="appversion",
            name="is_silent",
            field=models.BooleanField(default=False, verbose_name="是否静默更新"),
        ),
        migrations.AddField(
            model_name="appversion",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="是否启用"),
        ),
        migrations.AddField(
            model_name="appversion",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="创建时间",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(map_legacy_force_flag, restore_legacy_force_flag),
        migrations.RemoveField(
            model_name="appversion",
            name="is_forced",
        ),
        migrations.AlterField(
            model_name="appversion",
            name="update_type",
            field=models.IntegerField(
                choices=[
                    (0, "提示热更"),
                    (1, "强制热更"),
                    (2, "提示整包"),
                    (3, "强制整包"),
                ],
                default=0,
                verbose_name="更新类型",
            ),
        ),
        migrations.AlterField(
            model_name="appversion",
            name="platform",
            field=models.CharField(
                choices=[("Android", "Android"), ("iOS", "iOS")],
                max_length=20,
                verbose_name="平台类型",
            ),
        ),
        migrations.AlterField(
            model_name="appversion",
            name="download_url",
            field=models.URLField(max_length=500, verbose_name="下载包URL"),
        ),
        migrations.AlterField(
            model_name="appversion",
            name="changelog",
            field=models.TextField(blank=True, default="", verbose_name="更新日志说明"),
        ),
        migrations.AlterModelOptions(
            name="appversion",
            options={
                "ordering": ["-version_code", "-created_at"],
                "verbose_name": "应用版本",
                "verbose_name_plural": "应用版本",
            },
        ),
        migrations.AddIndex(
            model_name="appversion",
            index=models.Index(
                fields=["platform", "is_active"],
                name="appver_platform_active_idx",
            ),
        ),
    ]

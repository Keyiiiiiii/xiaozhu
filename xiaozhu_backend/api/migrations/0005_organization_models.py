import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_sync_appversion_schema"),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
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
                    models.CharField(max_length=50, unique=True, verbose_name="部门编码"),
                ),
                ("name", models.CharField(max_length=100, verbose_name="部门名称")),
            ],
            options={
                "verbose_name": "部门",
                "verbose_name_plural": "部门",
                "ordering": ["code"],
            },
        ),
        migrations.CreateModel(
            name="District",
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
                    models.CharField(max_length=50, unique=True, verbose_name="区县编码"),
                ),
                ("name", models.CharField(max_length=100, verbose_name="区县名称")),
            ],
            options={
                "verbose_name": "区县",
                "verbose_name_plural": "区县",
                "ordering": ["code"],
            },
        ),
        migrations.CreateModel(
            name="Grid",
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
                ("code", models.CharField(max_length=50, verbose_name="网格编码")),
                ("name", models.CharField(max_length=100, verbose_name="网格名称")),
                (
                    "district",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="grids",
                        to="api.district",
                        verbose_name="所属区县",
                    ),
                ),
            ],
            options={
                "verbose_name": "网格",
                "verbose_name_plural": "网格",
                "ordering": ["district_id", "code"],
            },
        ),
        migrations.AddConstraint(
            model_name="grid",
            constraint=models.UniqueConstraint(
                fields=("district", "code"),
                name="uniq_grid_code_per_district",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="users",
                to="api.department",
                verbose_name="所属部门",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="district",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="users",
                to="api.district",
                verbose_name="所属区县",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="grid",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="users",
                to="api.grid",
                verbose_name="所属网格",
            ),
        ),
    ]

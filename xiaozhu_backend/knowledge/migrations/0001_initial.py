# Generated manually to bring the existing KnowledgeFile model under migrations.
from django.db import migrations, models


def create_knowledge_file_table_if_missing(apps, schema_editor):
    from django.apps import apps as installed_apps

    KnowledgeFile = installed_apps.get_model("knowledge", "KnowledgeFile")
    table_name = KnowledgeFile._meta.db_table
    existing_tables = schema_editor.connection.introspection.table_names()
    if table_name not in existing_tables:
        schema_editor.create_model(KnowledgeFile)


def drop_knowledge_file_table_if_present(apps, schema_editor):
    from django.apps import apps as installed_apps

    KnowledgeFile = installed_apps.get_model("knowledge", "KnowledgeFile")
    table_name = KnowledgeFile._meta.db_table
    existing_tables = schema_editor.connection.introspection.table_names()
    if table_name in existing_tables:
        schema_editor.delete_model(KnowledgeFile)


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    create_knowledge_file_table_if_missing,
                    drop_knowledge_file_table_if_present,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="KnowledgeFile",
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
                            "file_name",
                            models.CharField(max_length=255, verbose_name="文件名"),
                        ),
                        (
                            "file_url",
                            models.URLField(max_length=500, verbose_name="文件URL"),
                        ),
                        (
                            "file_size",
                            models.IntegerField(verbose_name="文件大小(字节)"),
                        ),
                        (
                            "file_type",
                            models.CharField(max_length=100, verbose_name="文件类型"),
                        ),
                        (
                            "uploaded_at",
                            models.DateTimeField(
                                auto_now_add=True,
                                verbose_name="上传时间",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "知识库文件",
                        "verbose_name_plural": "知识库文件",
                    },
                ),
            ],
        ),
    ]

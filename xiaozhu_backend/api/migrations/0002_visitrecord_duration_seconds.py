from django.db import migrations


def add_duration_seconds_if_missing(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'api_visitrecord'
              AND COLUMN_NAME = 'duration_seconds'
            """
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "ALTER TABLE api_visitrecord "
                "ADD COLUMN duration_seconds integer UNSIGNED NULL"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            add_duration_seconds_if_missing,
            migrations.RunPython.noop,
        ),
    ]

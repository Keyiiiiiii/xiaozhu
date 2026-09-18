from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class NotificationAndVersionMigrationTests(TransactionTestCase):
    migrate_from = [("api", "0003_role_permission_and_todo")]
    migrate_to = [("api", "0006_notification_delivery_models")]

    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        Role = old_apps.get_model("api", "Role")
        User = old_apps.get_model("api", "User")
        Notification = old_apps.get_model("api", "Notification")
        AppVersion = old_apps.get_model("api", "AppVersion")

        role = Role.objects.create(code="legacy", name="旧角色", level=1)
        user = User.objects.create(
            username="legacy-user",
            password="unusable",
            work_id="LEGACY001",
            name="旧用户",
            role=role,
            organization="旧组织文本",
        )
        self.notification_id = Notification.objects.create(
            title="旧通知",
            content="旧正文",
            level=role,
            sender=user,
            status="unread",
        ).id
        self.version_id = AppVersion.objects.create(
            platform="Android",
            version="0.9.0",
            download_url="https://example.com/legacy.apk",
            is_forced=True,
            changelog="旧版本",
        ).id

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_legacy_records_are_preserved_and_safely_mapped(self):
        Notification = self.apps.get_model("api", "Notification")
        NotificationReceiver = self.apps.get_model("api", "NotificationReceiver")
        AppVersion = self.apps.get_model("api", "AppVersion")

        notification = Notification.objects.get(id=self.notification_id)
        self.assertEqual(notification.status, "revoked")
        self.assertEqual(notification.level, "normal")
        self.assertEqual(notification.scope, "city")
        self.assertIsNotNone(notification.revoked_at)
        self.assertFalse(
            NotificationReceiver.objects.filter(notification=notification).exists()
        )

        version = AppVersion.objects.get(id=self.version_id)
        self.assertEqual(version.version_code, 0)
        self.assertEqual(version.update_type, 3)
        self.assertTrue(version.is_active)
        self.assertFalse(version.is_silent)

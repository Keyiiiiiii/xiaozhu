from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from api.models import (
    District,
    Grid,
    Notification,
    NotificationReceiver,
    Role,
    User,
)
from api.notification_services import (
    acknowledge_force_notification,
    mark_notification_read,
    pending_force_notifications,
    publish_notification,
)


class NotificationModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_test_users", verbosity=0)
        cls.city_user = User.objects.get(work_id="FZ10000")
        cls.district_user = User.objects.get(work_id="FZ10086")
        cls.frontline_user = User.objects.get(work_id="admin")
        cls.gulou = District.objects.get(code="gulou")
        cls.second_grid = Grid.objects.get(code="grid_2", district=cls.gulou)

        frontline_role = Role.objects.get(code="frontline")
        cls.gulou_frontline = User.objects.create_user(
            username="FZ20001",
            work_id="FZ20001",
            password="123456",
            name="鼓楼一线",
            role=frontline_role,
            organization="市公司 / 鼓楼区 / 第二网格",
            district=cls.gulou,
            grid=cls.second_grid,
        )
        cls.inactive_frontline = User.objects.create_user(
            username="FZ20002",
            work_id="FZ20002",
            password="123456",
            name="停用一线",
            role=frontline_role,
            organization="市公司 / 鼓楼区 / 第二网格",
            district=cls.gulou,
            grid=cls.second_grid,
            is_active=False,
        )

    def test_seed_users_have_normalized_organizations(self):
        self.assertEqual(self.frontline_user.district.code, "test_district")
        self.assertEqual(self.frontline_user.grid.code, "grid_1")
        self.assertEqual(self.district_user.district.code, "gulou")
        self.assertIsNone(self.district_user.grid)
        self.assertEqual(self.city_user.department.code, "city_hq")
        self.assertTrue(
            self.city_user.role.permissions.filter(code="notify.receive").exists()
        )

    def test_seed_test_users_is_idempotent(self):
        counts_before = {
            "users": User.objects.filter(
                work_id__in=["admin", "FZ10086", "FZ10000"]
            ).count(),
            "districts": District.objects.count(),
            "grids": Grid.objects.count(),
        }
        call_command("seed_test_users", verbosity=0)
        counts_after = {
            "users": User.objects.filter(
                work_id__in=["admin", "FZ10086", "FZ10000"]
            ).count(),
            "districts": District.objects.count(),
            "grids": Grid.objects.count(),
        }
        self.assertEqual(counts_after, counts_before)

    def test_user_validation_rejects_grid_from_another_district(self):
        self.frontline_user.district = self.gulou
        with self.assertRaises(ValidationError):
            self.frontline_user.full_clean()

    def test_notification_validation_rejects_invalid_force_rule(self):
        notification = Notification(
            title="错误配置",
            content="正文",
            level="urgent",
            scope="city",
            publisher=self.city_user,
            force_display=True,
            force_duration=3,
        )
        with self.assertRaises(ValidationError):
            notification.full_clean()

    def test_database_rejects_invalid_scope_targets(self):
        with self.assertRaises(IntegrityError):
            Notification.objects.create(
                title="错误范围",
                content="正文",
                level="normal",
                scope="district",
                publisher=self.city_user,
                force_display=False,
                force_duration=0,
            )

    def test_city_scope_creates_receiver_snapshot_for_active_receivers(self):
        notification = publish_notification(
            publisher=self.city_user,
            title="全市通知",
            content="正文",
            level="normal",
            scope="city",
        )
        receiver_ids = set(
            notification.receivers.values_list("user__work_id", flat=True)
        )
        self.assertSetEqual(
            receiver_ids,
            {"admin", "FZ10086", "FZ10000", "FZ20001"},
        )
        self.assertNotIn("FZ20002", receiver_ids)

    def test_district_and_grid_scopes_do_not_cross_organization_boundaries(self):
        district_notice = publish_notification(
            publisher=self.city_user,
            title="鼓楼通知",
            content="正文",
            level="important",
            scope="district",
            target_district=self.gulou,
        )
        self.assertSetEqual(
            set(district_notice.receivers.values_list("user__work_id", flat=True)),
            {"FZ10086", "FZ20001"},
        )

        grid_notice = publish_notification(
            publisher=self.district_user,
            title="第二网格通知",
            content="正文",
            level="urgent",
            scope="grid",
            target_district=self.gulou,
            target_grid=self.second_grid,
        )
        self.assertSetEqual(
            set(grid_notice.receivers.values_list("user__work_id", flat=True)),
            {"FZ20001"},
        )
        self.assertTrue(grid_notice.force_display)
        self.assertEqual(grid_notice.force_duration, 10)

    def test_district_publisher_cannot_publish_outside_allowed_grid_scope(self):
        with self.assertRaises(PermissionDenied):
            publish_notification(
                publisher=self.district_user,
                title="越权通知",
                content="正文",
                level="normal",
                scope="city",
            )

        test_district = District.objects.get(code="test_district")
        first_grid = Grid.objects.get(code="grid_1", district=test_district)
        with self.assertRaises(PermissionDenied):
            publish_notification(
                publisher=self.district_user,
                title="跨区通知",
                content="正文",
                level="normal",
                scope="grid",
                target_district=test_district,
                target_grid=first_grid,
            )

    def test_read_and_force_ack_are_independent_and_idempotent(self):
        notification = publish_notification(
            publisher=self.city_user,
            title="重要通知",
            content="正文",
            level="important",
            scope="city",
        )
        first = mark_notification_read(notification, self.frontline_user)
        first_read_at = first.read_at
        second = mark_notification_read(notification, self.frontline_user)
        self.assertEqual(second.read_at, first_read_at)

        other_receiver = NotificationReceiver.objects.get(
            notification=notification,
            user=self.district_user,
        )
        self.assertIsNone(other_receiver.read_at)

        first_ack = acknowledge_force_notification(notification, self.frontline_user)
        first_ack_at = first_ack.force_ack_at
        second_ack = acknowledge_force_notification(notification, self.frontline_user)
        self.assertEqual(second_ack.force_ack_at, first_ack_at)

    def test_pending_force_excludes_acknowledged_expired_and_revoked(self):
        active = publish_notification(
            publisher=self.city_user,
            title="待展示",
            content="正文",
            level="important",
            scope="city",
        )
        acknowledged = publish_notification(
            publisher=self.city_user,
            title="已确认",
            content="正文",
            level="urgent",
            scope="city",
        )
        acknowledge_force_notification(acknowledged, self.frontline_user)

        now = timezone.now()
        expired = Notification.objects.create(
            title="已过期",
            content="正文",
            level="important",
            scope="city",
            publisher=self.city_user,
            force_display=True,
            force_duration=3,
            published_at=now - timedelta(days=2),
            expire_at=now - timedelta(days=1),
        )
        NotificationReceiver.objects.create(
            notification=expired,
            user=self.frontline_user,
        )
        revoked = publish_notification(
            publisher=self.city_user,
            title="已撤回",
            content="正文",
            level="urgent",
            scope="city",
        )
        revoked.status = "revoked"
        revoked.revoked_at = now
        revoked.save(update_fields=["status", "revoked_at"])

        pending_ids = set(
            pending_force_notifications(self.frontline_user).values_list(
                "id",
                flat=True,
            )
        )
        self.assertIn(active.id, pending_ids)
        self.assertNotIn(acknowledged.id, pending_ids)
        self.assertNotIn(expired.id, pending_ids)
        self.assertNotIn(revoked.id, pending_ids)

    def test_receiver_unique_constraint(self):
        notification = publish_notification(
            publisher=self.city_user,
            title="唯一约束",
            content="正文",
            level="normal",
            scope="city",
        )
        with self.assertRaises(IntegrityError):
            NotificationReceiver.objects.create(
                notification=notification,
                user=self.frontline_user,
            )

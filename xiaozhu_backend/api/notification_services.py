from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from api.models import Notification, NotificationReceiver, User


FORCE_RULES = {
    "normal": (False, 0),
    "important": (True, 3),
    "urgent": (True, 10),
}


def notification_recipients(notification):
    """Return active users eligible to receive a notification snapshot."""
    users = User.objects.filter(
        is_active=True,
        role__permissions__code="notify.receive",
    ).distinct()

    if notification.scope == "district":
        users = users.filter(district_id=notification.target_district_id)
    elif notification.scope == "grid":
        users = users.filter(
            district_id=notification.target_district_id,
            grid_id=notification.target_grid_id,
        )
    return users


def _validate_publish_permission(publisher, scope, target_district):
    role_code = publisher.role.code if publisher.role_id else None
    if role_code == "city":
        return
    if role_code == "district":
        if scope != "grid":
            raise PermissionDenied("区县专项只能向网格发布通知。")
        if (
            not publisher.district_id
            or publisher.district_id != getattr(target_district, "id", None)
        ):
            raise PermissionDenied("区县专项只能向本区县网格发布通知。")
        return
    raise PermissionDenied("当前用户无权发布通知。")


@transaction.atomic
def publish_notification(
    *,
    publisher,
    title,
    content,
    level,
    scope,
    target_district=None,
    target_grid=None,
    expire_at=None,
):
    """Create a published notification and its immutable receiver snapshot."""
    _validate_publish_permission(publisher, scope, target_district)
    try:
        force_display, force_duration = FORCE_RULES[level]
    except KeyError as exc:
        raise ValidationError({"level": "未知的通知级别。"}) from exc
    notification = Notification(
        title=title,
        content=content,
        level=level,
        scope=scope,
        target_district=target_district,
        target_grid=target_grid,
        publisher=publisher,
        force_display=force_display,
        force_duration=force_duration,
        status="published",
        expire_at=expire_at,
    )
    notification.full_clean()
    notification.save()

    NotificationReceiver.objects.bulk_create(
        [
            NotificationReceiver(notification=notification, user=user)
            for user in notification_recipients(notification).iterator()
        ]
    )
    return notification


def mark_notification_read(notification, user, at=None):
    receiver = NotificationReceiver.objects.get(
        notification=notification,
        user=user,
    )
    if receiver.read_at is None:
        receiver.read_at = at or timezone.now()
        receiver.save(update_fields=["read_at"])
    return receiver


def acknowledge_force_notification(notification, user, at=None):
    receiver = NotificationReceiver.objects.get(
        notification=notification,
        user=user,
    )
    if receiver.force_ack_at is None:
        receiver.force_ack_at = at or timezone.now()
        receiver.save(update_fields=["force_ack_at"])
    return receiver


def pending_force_notifications(user, at=None):
    now = at or timezone.now()
    return Notification.objects.filter(
        receivers__user=user,
        receivers__force_ack_at__isnull=True,
        force_display=True,
        status="published",
    ).filter(Q(expire_at__isnull=True) | Q(expire_at__gt=now))

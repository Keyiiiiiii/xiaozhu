from django.core.management.base import BaseCommand

from api.models import Permission, Role, User

PERMISSIONS = [
    ("notify.receive", "接收通知"),
    ("notify.dispatch.frontline", "下达通知给一线"),
    ("notify.dispatch.district", "下达通知给区县专项"),
]

ROLES = [
    {
        "code": "frontline",
        "name": "一线人员",
        "level": 1,
        "permission_codes": ["notify.receive"],
    },
    {
        "code": "district",
        "name": "区县专项",
        "level": 2,
        "permission_codes": [
            "notify.receive",
            "notify.dispatch.frontline",
        ],
    },
    {
        "code": "city",
        "name": "市公司",
        "level": 3,
        "permission_codes": [
            "notify.dispatch.frontline",
            "notify.dispatch.district",
        ],
    },
]

SEED_USERS = [
    {
        "work_id": "admin",
        "password": "123456",
        "name": "张三",
        "role_code": "frontline",
        "organization": "市公司 / 政企客户部 / 第一网格",
    },
    {
        "work_id": "FZ10086",
        "password": "123456",
        "name": "李四",
        "role_code": "district",
        "organization": "市公司 / 鼓楼区 / 第二网格",
    },
    {
        "work_id": "FZ10000",
        "password": "123456",
        "name": "王五",
        "role_code": "city",
        "organization": "市公司",
    },
]


class Command(BaseCommand):
    help = "Seed roles, permissions, and test users (idempotent)."

    def handle(self, *args, **options):
        perm_map = {}
        for code, name in PERMISSIONS:
            perm, created = Permission.objects.update_or_create(
                code=code,
                defaults={"name": name},
            )
            perm_map[code] = perm
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} permission {code}"))

        role_map = {}
        for entry in ROLES:
            role, created = Role.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "name": entry["name"],
                    "level": entry["level"],
                },
            )
            role.permissions.set(
                [perm_map[code] for code in entry["permission_codes"]]
            )
            role_map[entry["code"]] = role
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} role {entry['code']}"))

        for entry in SEED_USERS:
            work_id = entry["work_id"]
            user, created = User.objects.update_or_create(
                work_id=work_id,
                defaults={
                    "username": work_id,
                    "name": entry["name"],
                    "role": role_map[entry["role_code"]],
                    "organization": entry["organization"],
                },
            )
            user.set_password(entry["password"])
            user.save()

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} user work_id={work_id} id={user.id} "
                    f"role={entry['role_code']}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. Test login: admin / 123456"
            )
        )

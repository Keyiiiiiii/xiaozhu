from django.core.management.base import BaseCommand

from api.models import User

SEED_USERS = [
    {
        "work_id": "admin",
        "password": "123456",
        "name": "张三",
        "role_id": "客户经理",
        "organization": "市公司 / 政企客户部 / 第一网格",
    },
    {
        "work_id": "FZ10086",
        "password": "123456",
        "name": "李四",
        "role_id": "网格长",
        "organization": "市公司 / 鼓楼区 / 第二网格",
    },
]


class Command(BaseCommand):
    help = "Seed test users for login and API testing (idempotent)."

    def handle(self, *args, **options):
        for entry in SEED_USERS:
            work_id = entry["work_id"]
            user, created = User.objects.update_or_create(
                work_id=work_id,
                defaults={
                    "username": work_id,
                    "name": entry["name"],
                    "role_id": entry["role_id"],
                    "organization": entry["organization"],
                },
            )
            user.set_password(entry["password"])
            user.save()

            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} user work_id={work_id} id={user.id} "
                    f"(login with work_id or username, password from seed)"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. Test login: admin / 123456"
            )
        )

from django.core.management.base import BaseCommand

from api.models import AppVersion

# 测试版本数据：覆盖四种 update_type + 跨平台
SEED_VERSIONS = [
    {
        "platform": "Android",
        "version": "1.0.0",
        "version_code": 100,
        "update_type": 0,
        "download_url": "http://localhost:8000/static/wgt/xiaozhu_v1.0.0.wgt",
        "changelog": "初始版本",
        "is_silent": False,
        "is_active": True,
    },
    {
        "platform": "Android",
        "version": "1.1.0",
        "version_code": 110,
        "update_type": 0,  # 提示热更
        "download_url": "http://localhost:8000/static/wgt/xiaozhu_v1.1.0.wgt",
        "changelog": "1. 修复走访录音上传偶发失败问题\n2. 优化工作台通知展示",
        "is_silent": False,
        "is_active": True,
    },
    {
        "platform": "Android",
        "version": "1.2.0",
        "version_code": 120,
        "update_type": 2,  # 提示整包
        "download_url": "http://localhost:8000/static/apk/xiaozhu_v1.2.0.apk",
        "changelog": "新增知识库智能问答与待办联动，需要下载整包更新",
        "is_silent": False,
        "is_active": True,
    },
    {
        "platform": "iOS",
        "version": "1.0.0",
        "version_code": 100,
        "update_type": 0,
        "download_url": "itms-apps://apps.apple.com/app/id000000000",
        "changelog": "iOS 初始版本",
        "is_silent": False,
        "is_active": True,
    },
]


class Command(BaseCommand):
    help = "Seed test app versions for version-check API (idempotent)."

    def handle(self, *args, **options):
        for entry in SEED_VERSIONS:
            platform = entry["platform"]
            version_code = entry["version_code"]
            obj, created = AppVersion.objects.update_or_create(
                platform=platform,
                version_code=version_code,
                defaults={
                    "version": entry["version"],
                    "update_type": entry["update_type"],
                    "download_url": entry["download_url"],
                    "changelog": entry["changelog"],
                    "is_silent": entry["is_silent"],
                    "is_active": entry["is_active"],
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{action} AppVersion {platform} v{obj.version} "
                    f"(code={obj.version_code}, type={obj.update_type})"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. Latest Android version_code: "
                f"{max(v['version_code'] for v in SEED_VERSIONS if v['platform'] == 'Android')}"
            )
        )

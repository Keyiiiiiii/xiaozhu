import json

from django.core.management import call_command
from django.test import TestCase, Client

from api.models import AppVersion


class VersionCheckApiTests(TestCase):
    def setUp(self):
        call_command("seed_app_versions")
        self.client = Client()

    def _post(self, payload):
        return self.client.post(
            "/api/version/check/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_check_update_no_new_version(self):
        """客户端已是最新 Android 版本 -> data 为 null"""
        response = self._post({
            "platform": "Android",
            "version": "1.2.0",
            "versionCode": 120,
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertIsNone(body["data"])

    def test_check_update_discover_wgt(self):
        """客户端版本低于 Android 最新 -> 返回最新版本（提示热更）"""
        response = self._post({
            "platform": "Android",
            "version": "1.0.0",
            "versionCode": 100,
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        data = body["data"]
        self.assertIsNotNone(data)
        self.assertEqual(data["version"], "1.2.0")
        self.assertEqual(data["version_code"], 120)
        self.assertEqual(data["update_type"], 2)
        self.assertEqual(data["platform"], "Android")
        self.assertIn("download_url", data)
        self.assertIn("update_log", data)

    def test_check_update_ios_platform(self):
        """iOS 平台查询应独立返回 iOS 最新版本"""
        response = self._post({
            "platform": "iOS",
            "version": "1.0.0",
            "versionCode": 100,
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        data = body["data"]
        self.assertIsNone(data)  # iOS 仅有 100 版本，已是最新

    def test_check_update_platform_normalization(self):
        """平台字符串大小写不敏感"""
        response = self._post({
            "platform": "android",
            "version": "1.0.0",
            "versionCode": 100,
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["platform"], "Android")

    def test_check_update_missing_platform(self):
        response = self._post({"version": "1.0.0", "versionCode": 100})
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["status"], "error")

    def test_check_update_missing_version(self):
        response = self._post({"platform": "Android", "versionCode": 100})
        self.assertEqual(response.status_code, 400)

    def test_check_update_inactive_version_skipped(self):
        """is_active=False 的版本不应被返回"""
        AppVersion.objects.filter(platform="Android", version_code=120).update(
            is_active=False
        )
        response = self._post({
            "platform": "Android",
            "version": "1.0.0",
            "versionCode": 100,
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        # 最新启用版本变为 1.1.0 (110)，应该返回它
        self.assertEqual(body["data"]["version_code"], 110)

    def test_check_update_invalid_version_code(self):
        """非法 versionCode 库容错为 0"""
        response = self._post({
            "platform": "Android",
            "version": "1.0.0",
            "versionCode": "abc",
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["version_code"], 120)

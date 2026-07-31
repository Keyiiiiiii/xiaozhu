import json

from django.core.management import call_command
from django.test import TestCase, Client


class AuthApiTests(TestCase):
    def setUp(self):
        call_command("seed_test_users")
        self.client = Client()

    def _login(self):
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "admin", "password": "123456"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("token", data["data"])
        self.assertIn("userInfo", data["data"])
        return data["data"]

    def test_login_success(self):
        data = self._login()
        self.assertEqual(data["userInfo"]["empId"], "admin")
        self.assertTrue(data["token"])

    def test_login_wrong_password(self):
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "admin", "password": "wrong"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_me_without_token(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_me_with_token(self):
        login_data = self._login()
        token = login_data["token"]
        response = self.client.get(
            "/api/auth/me/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["data"]["userInfo"]["empId"], "admin")

    def test_refresh_token(self):
        login_data = self._login()
        response = self.client.post(
            "/api/auth/refresh/",
            data=json.dumps({"refresh": login_data["refresh"]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertIn("token", body["data"])

    def test_record_ids_without_token(self):
        response = self.client.post("/api/file/record-ids/")
        self.assertEqual(response.status_code, 401)

    def test_record_ids_with_token(self):
        login_data = self._login()
        token = login_data["token"]
        response = self.client.post(
            "/api/file/record-ids/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")

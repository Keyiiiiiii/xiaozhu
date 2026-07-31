import json

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from api.auth_utils import get_user_from_request


def serialize_user(user):
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "role": user.role_id,
        "dept": user.organization,
        "empId": user.work_id,
    }


def _parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    data = _parse_json_body(request)
    username = (data.get("username") or request.POST.get("username") or "").strip()
    password = data.get("password") or request.POST.get("password") or ""

    if not username or not password:
        return JsonResponse(
            {"status": "error", "message": "账号和密码不能为空"},
            status=400,
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse(
            {"status": "error", "message": "账号或密码错误"},
            status=401,
        )

    refresh = RefreshToken.for_user(user)
    return JsonResponse(
        {
            "status": "success",
            "message": "登录成功",
            "data": {
                "token": str(refresh.access_token),
                "refresh": str(refresh),
                "userInfo": serialize_user(user),
            },
        }
    )


@csrf_exempt
@require_http_methods(["GET"])
def me_view(request):
    user = get_user_from_request(request)
    if user is None:
        return JsonResponse(
            {"status": "error", "message": "未登录或 token 无效"},
            status=401,
        )

    return JsonResponse(
        {
            "status": "success",
            "message": "获取成功",
            "data": {
                "userInfo": serialize_user(user),
            },
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def refresh_view(request):
    data = _parse_json_body(request)
    refresh_token = (
        data.get("refresh")
        or request.POST.get("refresh")
        or ""
    ).strip()

    if not refresh_token:
        return JsonResponse(
            {"status": "error", "message": "refresh token 不能为空"},
            status=400,
        )

    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
    except TokenError:
        return JsonResponse(
            {"status": "error", "message": "refresh token 无效或已过期"},
            status=401,
        )

    return JsonResponse(
        {
            "status": "success",
            "message": "刷新成功",
            "data": {
                "token": access_token,
            },
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    # MVP: client clears token; optional server-side blacklist omitted.
    return JsonResponse({"status": "success", "message": "登出成功"})

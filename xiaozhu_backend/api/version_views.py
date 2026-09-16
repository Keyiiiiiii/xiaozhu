import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from api.models import AppVersion


def _parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _normalize_platform(raw):
    """Normalize platform string from client (e.g. 'android', 'ANDROID', 'ios')."""
    if not raw:
        return ""
    value = str(raw).strip().lower()
    if value in ("ios", "iphone", "ipad"):
        return "iOS"
    if value in ("android", "apk"):
        return "Android"
    return ""


def _parse_version_code(raw):
    if raw is None or raw == "":
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _serialize_version(app_version):
    """Serialize AppVersion for client consumption."""
    return {
        "version": app_version.version,
        "version_code": app_version.version_code,
        "update_type": app_version.update_type,
        "download_url": app_version.download_url,
        "update_log": app_version.changelog or "",
        "is_silent": app_version.is_silent,
        "platform": app_version.platform,
    }


@csrf_exempt
@require_http_methods(["POST"])
def check_update_view(request):
    """
    POST /api/version/check/

    Request body (JSON):
        {
            "platform": "Android" | "iOS",
            "version": "1.0.0",
            "versionCode": 100
        }

    Response (JSON):
        {
            "status": "success",
            "message": "...",
            "data": {
                "version": "1.1.0",
                "version_code": 110,
                "update_type": 0,         # 0:提示热更 1:强制热更 2:提示整包 3:强制整包
                "download_url": "...",
                "update_log": "...",
                "is_silent": false,
                "platform": "Android"
            } | null
        }
    """
    data = _parse_json_body(request)
    platform = _normalize_platform(data.get("platform"))
    version = (data.get("version") or "").strip()
    version_code = _parse_version_code(data.get("versionCode"))

    if not platform:
        return JsonResponse(
            {"status": "error", "message": "platform 不能为空 (Android / iOS)"},
            status=400,
        )
    if not version:
        return JsonResponse(
            {"status": "error", "message": "version 不能为空"},
            status=400,
        )

    # 选择当前平台启用中的最新版本（version_code 最大者）
    latest = (
        AppVersion.objects
        .filter(platform=platform, is_active=True)
        .order_by("-version_code", "-created_at")
        .first()
    )

    if latest is None or latest.version_code <= version_code:
        return JsonResponse(
            {
                "status": "success",
                "message": "当前已是最新版本",
                "data": None,
            }
        )

    return JsonResponse(
        {
            "status": "success",
            "message": "发现新版本",
            "data": _serialize_version(latest),
        }
    )

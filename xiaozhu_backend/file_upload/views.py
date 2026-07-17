import uuid
import os
import time
import requests
from io import BytesIO
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .minio_client import upload_file_to_minio, get_file_from_minio
from api.models import VisitRecord, User

AUDIO_CONTENT_TYPES = {
    ".m4a": "audio/m4a",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}

STATUS_MAP = {
    1: "pending",
    2: "processing",
    3: "success",
    4: "failed",
}


def get_content_type(object_name):
    _, ext = os.path.splitext(object_name)
    return AUDIO_CONTENT_TYPES.get(ext.lower(), "audio/m4a")


@csrf_exempt
@require_POST
def upload_file(request):
    file_keys = list(request.FILES.keys())

    uploaded_file = None
    for key in ["file", "files", "file[]", "files[]"]:
        if key in request.FILES:
            uploaded_file = request.FILES[key]
            break

    if uploaded_file is None:
        return JsonResponse(
            {"status": "error", "message": f"没有找到文件，接收到的字段: {file_keys}"},
            status=400
        )

    if not uploaded_file.name:
        return JsonResponse(
            {"status": "error", "message": "文件名不能为空"},
            status=400
        )

    _, ext = os.path.splitext(uploaded_file.name)
    object_name = f"{uuid.uuid4().hex}{ext}"

    result = upload_file_to_minio(uploaded_file, object_name)

    if result["success"]:
        creator_id = int(request.POST.get("creator_id", 1))
        customer_name = request.POST.get("customer_name", "cus")
        visit_time_str = request.POST.get("visit_time", "2026-07-01")
        status = int(request.POST.get("status", 1))

        try:
            visit_time = datetime.strptime(visit_time_str, "%Y-%m-%d")
        except ValueError:
            visit_time = datetime.now()

        status_str = STATUS_MAP.get(status, "pending")

        try:
            creator = User.objects.get(id=creator_id)
        except User.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": f"用户ID {creator_id} 不存在"
            }, status=400)

        visit_record = VisitRecord.objects.create(
            creator=creator,
            customer_name=customer_name,
            audio_url=result["url"],
            visit_time=visit_time,
            status=status_str
        )

        return JsonResponse({
            "status": "success",
            "message": "文件上传成功",
            "file_url": result["url"],
            "record_id": visit_record.id
        })
    else:
        return JsonResponse({
            "status": "error",
            "message": f"文件上传失败: {result['error']}"
        }, status=500)


@csrf_exempt
@require_POST
def speech_to_text(request):
    creator_id = int(request.POST.get("creator_id", 1))
    record_id = int(request.POST.get("id", 1))

    try:
        visit_record = VisitRecord.objects.get(id=record_id, creator_id=creator_id)
    except VisitRecord.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": f"走访记录 ID={record_id}, creator_id={creator_id} 不存在"
        }, status=400)

    file_url = visit_record.audio_url

    if not file_url:
        return JsonResponse(
            {"status": "error", "message": "该走访记录没有关联的音频文件URL"},
            status=400
        )

    minio_result = get_file_from_minio(file_url)

    if not minio_result["success"]:
        return JsonResponse({
            "status": "error",
            "message": f"从MinIO获取文件失败: {minio_result['error']}"
        }, status=500)

    file_content = minio_result["content"]
    object_name = minio_result["object_name"]

    try:
        headers = {}
        if settings.ASR_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.ASR_API_TOKEN}"

        response = requests.post(
            settings.ASR_API_URL,
            headers=headers,
            data={"language": settings.ASR_LANGUAGE},
            files={"file": (object_name, BytesIO(file_content))},
            timeout=120
        )

        response.raise_for_status()
        job_id = response.json()["job_id"]

        visit_record.status = "processing"
        visit_record.save()

        while True:
            time.sleep(5)
            response = requests.get(
                f"{settings.ASR_API_URL}/{job_id}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            job = response.json()
            print(job["status"])
            if job["status"] == "done":
                break
            if job["status"] == "failed":
                visit_record.status = "failed"
                visit_record.save()
                raise RuntimeError(f"转写失败: {job}")

        requests.delete(
            f"{settings.ASR_API_URL}/{job_id}",
            headers=headers,
            timeout=30
        )

        visit_record.original_text = job.get("segments", "")
        visit_record.status = job.get("status", "")
        visit_record.save()

        return JsonResponse({
            "status": "success",
            "data": job
        })
    except RuntimeError as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"调用语音转文字API失败: {str(e)}"
        }, status=500)

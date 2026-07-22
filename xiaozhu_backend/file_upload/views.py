import uuid
import os
import time
import threading
import requests
from io import BytesIO
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import close_old_connections
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .minio_client import upload_file_to_minio, get_file_from_minio
from .askApi import call_llm_api, parse_llm_response, API_URL, API_KEY
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


def poll_asr_job(job_id, record_id, headers):
    max_poll_count = 120
    poll_count = 0

    try:
        while poll_count < max_poll_count:
            poll_count += 1
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
                requests.delete(
                    f"{settings.ASR_API_URL}/{job_id}",
                    headers=headers,
                    timeout=30
                )
                visit_record = VisitRecord.objects.get(id=record_id)
                visit_record.original_text = job
                visit_record.status = "success"
                visit_record.save()

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"asr_{job_id}",
                    {
                        "type": "asr_result",
                        "message": {
                            "status": "success",
                            "data": job
                        }
                    }
                )
                break

            if job["status"] == "failed":
                visit_record = VisitRecord.objects.get(id=record_id)
                visit_record.status = "failed"
                visit_record.save()

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"asr_{job_id}",
                    {
                        "type": "asr_result",
                        "message": {
                            "status": "error",
                            "message": f"转写失败: {job}"
                        }
                    }
                )
                break
        else:
            visit_record = VisitRecord.objects.get(id=record_id)
            visit_record.status = "failed"
            visit_record.save()

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"asr_{job_id}",
                {
                    "type": "asr_result",
                    "message": {
                        "status": "error",
                        "message": f"转写超时: 超过 {max_poll_count * 5} 秒"
                    }
                }
            )
    except Exception as e:
        try:
            visit_record = VisitRecord.objects.get(id=record_id)
            visit_record.status = "failed"
            visit_record.save()
        except VisitRecord.DoesNotExist:
            pass

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"asr_{job_id}",
            {
                "type": "asr_result",
                "message": {
                    "status": "error",
                    "message": f"调用语音转文字API失败: {str(e)}"
                }
            }
        )
    finally:
        close_old_connections()


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

        thread = threading.Thread(
            target=poll_asr_job,
            args=(job_id, record_id, headers),
            daemon=True
        )
        thread.start()

        return JsonResponse({
            "status": "success",
            "message": "转写任务已提交",
            "job_id": job_id,
            "record_id": record_id
        })
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"调用语音转文字API失败: {str(e)}"
        }, status=500)


@csrf_exempt
@require_POST
def summarize_record(request):
    creator_id = int(request.POST.get("creator_id", 0))
    record_id = int(request.POST.get("id", 0))

    if not creator_id or not record_id:
        return JsonResponse({
            "status": "error",
            "message": "id 和 record_id 不能为空。"
        }, status=400)

    try:
        visit_record = VisitRecord.objects.get(id=record_id, creator_id=creator_id)
    except VisitRecord.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": f"走访记录 ID={record_id}, creator_id={creator_id} 不存在"
        }, status=400)

    original_text = visit_record.original_text
    if not original_text or not original_text.strip():
        return JsonResponse({
            "status": "error",
            "message": "原始转写文本为空，无法进行总结"
        }, status=400)

    try:
        response = call_llm_api(API_URL, API_KEY, original_text, str(creator_id), False)

        if isinstance(response, str):
            return JsonResponse({
                "status": "error",
                "message": f"调用总结API失败: {response}"
            }, status=500)

        raw_text = response["data"]["data"]["outputs"]["text"]
        parsed_data = parse_llm_response(raw_text)
        ai_summary = parsed_data.get("summary", "")

        visit_record.ai_summary = ai_summary
        visit_record.save()

        return JsonResponse({
            "status": "success",
            "message": "总结成功",
            "ai_summary": ai_summary,
            "record_id": record_id
        })
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            "status": "error",
            "message": f"调用总结API失败: {str(e)}"
        }, status=500)
    except KeyError as e:
        return JsonResponse({
            "status": "error",
            "message": f"总结API响应格式错误: {str(e)}"
        }, status=500)


@csrf_exempt
@require_POST
def get_record_ids(request):
    creator_id = int(request.POST.get("creator_id", 0))

    if not creator_id:
        return JsonResponse({
            "status": "error",
            "message": "creator_id 不能为空"
        }, status=400)

    records = VisitRecord.objects.filter(creator_id=creator_id)
    record_ids = [record.id for record in records]

    return JsonResponse({
        "status": "success",
        "message": "获取成功",
        "record_ids": record_ids
    })


@csrf_exempt
@require_POST
def get_record_detail(request):
    creator_id = int(request.POST.get("creator_id", 0))
    record_id = int(request.POST.get("id", 0))

    if not creator_id or not record_id:
        return JsonResponse({
            "status": "error",
            "message": "creator_id 和 id 不能为空"
        }, status=400)

    try:
        visit_record = VisitRecord.objects.get(id=record_id, creator_id=creator_id)
    except VisitRecord.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": f"走访记录 ID={record_id}, creator_id={creator_id} 不存在"
        }, status=400)

    return JsonResponse({
        "status": "success",
        "message": "获取成功",
        "data": {
            "id": visit_record.id,
            "creator_id": visit_record.creator_id,
            "customer_name": visit_record.customer_name,
            "audio_url": visit_record.audio_url,
            "original_text": visit_record.original_text,
            "ai_summary": visit_record.ai_summary,
            "visit_time": visit_record.visit_time.isoformat() if visit_record.visit_time else None,
            "business_type": visit_record.business_type,
            "status": visit_record.status
        }
    })


@csrf_exempt
@require_POST
def update_original_text(request):
    creator_id = int(request.POST.get("creator_id", 0))
    record_id = int(request.POST.get("id", 0))
    original_text = request.POST.get("original_text", "")

    if not creator_id or not record_id:
        return JsonResponse({
            "status": "error",
            "message": "creator_id 和 id 不能为空"
        }, status=400)

    if not original_text or not original_text.strip():
        return JsonResponse({
            "status": "error",
            "message": "original_text 不能为空"
        }, status=400)

    try:
        visit_record = VisitRecord.objects.get(id=record_id, creator_id=creator_id)
    except VisitRecord.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": f"走访记录 ID={record_id}, creator_id={creator_id} 不存在"
        }, status=400)

    visit_record.original_text = original_text
    visit_record.save()

    return JsonResponse({
        "status": "success",
        "message": "更新成功",
        "record_id": record_id
    })

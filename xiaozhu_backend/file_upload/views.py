import uuid
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .minio_client import upload_file_to_minio


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
        return JsonResponse({
            "status": "success",
            "message": "文件上传成功",
            "file_url": result["url"]
        })
    else:
        return JsonResponse({
            "status": "error",
            "message": f"文件上传失败: {result['error']}"
        }, status=500)
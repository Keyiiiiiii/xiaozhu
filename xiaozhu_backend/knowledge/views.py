import json
import uuid
import os
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from file_upload.minio_client import upload_file_to_minio
from .services import call_knowledge_api_streaming, call_knowledge_api_non_streaming, extract_workflow_result
from .models import KnowledgeFile


@csrf_exempt
@require_POST
def knowledge_api(request):
    try:
        data = json.loads(request.body)
        
        question = data.get("ques", "")
        stream_param = data.get("stream", False)
        stream = bool(stream_param)
        user_id = data.get("sys.user_id", "")
        app_id = data.get("sys.app_id", "")
        workflow_id = data.get("sys.workflow_id", "")
        workflow_run_id = data.get("sys.workflow_run_id", "")
        
        if not question:
            return JsonResponse({"content": "请输入问题"}, status=400)
        
        if stream:
            response = StreamingHttpResponse(
                call_knowledge_api_streaming(
                    question=question,
                    user_id=user_id,
                    app_id=app_id,
                    workflow_id=workflow_id,
                    workflow_run_id=workflow_run_id
                ),
                content_type="text/event-stream"
            )
            response['Cache-Control'] = 'no-cache'
            response['Connection'] = 'keep-alive'
            return response
        else:
            result = call_knowledge_api_non_streaming(
                question=question,
                user_id=user_id,
                app_id=app_id,
                workflow_id=workflow_id,
                workflow_run_id=workflow_run_id
            )
            
            if isinstance(result, dict):
                content = result.get("content", "") or result.get("msg", "") or \
                          result.get("result", "") or result.get("answer", "")
                if not content:
                    content = result.get("outputs", {}).get("result", "")
                if not content:
                    content = json.dumps(result, ensure_ascii=False)
            elif isinstance(result, str):
                content = result
            else:
                content = str(result)
            
            return JsonResponse({"content": content})
            
    except json.JSONDecodeError:
        return JsonResponse({"content": "请求体格式错误"}, status=400)
    except Exception as e:
        return JsonResponse({"content": str(e)}, status=500)


@csrf_exempt
@require_POST
def upload_knowledge_file(request):
    file_keys = list(request.FILES.keys())

    uploaded_files = []
    for key in ["file", "files", "file[]", "files[]"]:
        if key in request.FILES:
            if isinstance(request.FILES[key], list):
                uploaded_files.extend(request.FILES[key])
            else:
                uploaded_files.append(request.FILES[key])
            break

    if not uploaded_files:
        return JsonResponse(
            {"status": "error", "message": f"没有找到文件，接收到的字段: {file_keys}"},
            status=400
        )

    saved_records = []

    for uploaded_file in uploaded_files:
        if not uploaded_file.name:
            continue

        _, ext = os.path.splitext(uploaded_file.name)
        object_name = f"{uuid.uuid4().hex}{ext}"

        result = upload_file_to_minio(uploaded_file, object_name)

        if result["success"]:
            file_size = uploaded_file.size
            file_type = uploaded_file.content_type

            knowledge_file = KnowledgeFile.objects.create(
                file_name=uploaded_file.name,
                file_url=result["url"],
                file_size=file_size,
                file_type=file_type
            )

            saved_records.append({
                "file_name": uploaded_file.name,
                "file_url": result["url"],
                "file_size": file_size,
                "file_type": file_type,
                "record_id": knowledge_file.id
            })
        else:
            return JsonResponse({
                "status": "error",
                "message": f"文件 {uploaded_file.name} 上传失败: {result['error']}"
            }, status=500)

    return JsonResponse({
        "status": "success",
        "message": f"成功上传 {len(saved_records)} 个文件",
        "files": saved_records
    })

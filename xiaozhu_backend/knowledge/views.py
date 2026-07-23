import json
import uuid
import os
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from file_upload.minio_client import upload_file_to_minio, get_file_from_minio
from .services import call_knowledge_api_streaming, call_knowledge_api_non_streaming, extract_workflow_result, extract_source_files
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
            
            content = ""
            
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
            
            source_files = extract_source_files(content)
            
            file_records = []
            if source_files:
                file_records = get_files_by_titles(source_files)
            
            return JsonResponse({
                "content": content,
                "source_files": source_files,
                "file_records": file_records
            })
            
    except json.JSONDecodeError:
        return JsonResponse({"content": "请求体格式错误"}, status=400)
    except Exception as e:
        return JsonResponse({"content": str(e)}, status=500)


def get_files_by_titles(titles: list) -> list:
    file_records = []
    
    all_files = KnowledgeFile.objects.all()
    db_files = {f.id: f for f in all_files}
    db_file_names = {f.id: f.file_name.lower() for f in all_files}
    
    for title in titles:
        try:
            clean_title = title.strip()
            if clean_title.startswith('#'):
                clean_title = clean_title[1:].strip()
            
            title_lower = clean_title.lower()
            
            matched_ids = set()
            
            for file_id, db_name in db_file_names.items():
                if title_lower in db_name or db_name in title_lower:
                    matched_ids.add(file_id)
                    continue
                
                title_chars = set(clean_title)
                db_chars = set(db_name)
                if len(title_chars) > 3 and len(db_chars) > 3:
                    overlap = title_chars & db_chars
                    if len(overlap) >= min(len(title_chars), len(db_chars)) * 0.6:
                        matched_ids.add(file_id)
            
            for file_id in matched_ids:
                if file_id in db_files:
                    f = db_files[file_id]
                    full_name = f.file_name
                    if f.file_type and '.' not in full_name:
                        full_name = f"{f.file_name}.{f.file_type}"
                    file_records.append({
                        "id": f.id,
                        "file_name": full_name,
                        "file_url": f.file_url,
                        "file_size": f.file_size,
                        "file_type": f.file_type
                    })
        except Exception:
            pass
    
    seen = set()
    unique_records = []
    for f in file_records:
        if f['id'] not in seen:
            seen.add(f['id'])
            unique_records.append(f)
    
    return unique_records


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


@csrf_exempt
def download_file(request, file_id):
    try:
        knowledge_file = KnowledgeFile.objects.get(id=file_id)
        result = get_file_from_minio(knowledge_file.file_url)
        
        if result["success"]:
            import urllib.parse
            
            ext = knowledge_file.file_type
            if ext and '.' not in ext:
                ext = f'.{ext}'
            
            content_type = get_content_type(ext or knowledge_file.file_name)
            
            download_name = knowledge_file.file_name
            if ext and '.' not in download_name:
                download_name = f"{knowledge_file.file_name}{ext}"
            
            encoded_name = urllib.parse.quote(download_name.encode('utf-8'))
            
            response = HttpResponse(result["content"])
            response['Content-Type'] = content_type
            response['Content-Disposition'] = f'attachment; filename="{encoded_name}"; filename*=UTF-8\'\'{encoded_name}'
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            return response
        else:
            return JsonResponse({"status": "error", "message": result["error"]}, status=404)
    except KnowledgeFile.DoesNotExist:
        return JsonResponse({"status": "error", "message": "文件不存在"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def get_content_type(file_name):
    ext = os.path.splitext(file_name)[1].lower()
    mime_types = {
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
    }
    return mime_types.get(ext, 'application/octet-stream')

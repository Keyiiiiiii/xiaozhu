import json
import uuid
import os
import unicodedata
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
            source_files = []

            if isinstance(result, dict):
                # 直接使用 services 已从 metadata.file_name 提取的 source_files，
                # 不再用 extract_source_files(content) 覆盖（避免丢失真实文件名）
                source_files = result.get("source_files", []) or []
                content = result.get("content", "") or ""

                if not content:
                    content = result.get("msg", "") or result.get("result", "") or \
                              result.get("answer", "")
                if not content:
                    content = result.get("outputs", {}).get("result", "")
                if not content:
                    content = json.dumps(result, ensure_ascii=False)
            elif isinstance(result, str):
                content = result
            else:
                content = str(result)

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
    """
    根据文件名列表精确查询数据库文件记录。

    入参 titles 是从智能体返回的 metadata.file_name 中提取出的纯文件名
    （不带路径、不带扩展名，如 "弱电系统按建筑功能分类介绍"）。
    数据库 KnowledgeFile.file_name 存的也是不带路径、不带扩展名的纯文件名，
    扩展名存在 file_type 字段。
    """
    if not titles:
        return []

    all_files = list(KnowledgeFile.objects.all())
    db_index = {}
    for f in all_files:
        # NFKC 归一化：把 DB 中的兼容性字符也转为标准形式，确保与入参匹配
        key = unicodedata.normalize('NFKC', (f.file_name or "").strip().lower())
        if key:
            db_index.setdefault(key, []).append(f)

    matched_files = []
    seen_ids = set()

    for title in titles:
        if not title or not isinstance(title, str):
            continue

        clean = title.strip().lstrip('#').strip()
        # NFKC 归一化：入参也做同样的归一化
        clean = unicodedata.normalize('NFKC', clean)
        # 入参可能仍带扩展名（兜底），统一拆出 base_name + ext
        base_name, ext = os.path.splitext(clean)
        base_name = unicodedata.normalize('NFKC', base_name.strip())
        ext = ext.lstrip('.').strip().lower()

        if not base_name:
            continue

        # 1. 优先按 base_name 精确匹配（大小写不敏感 + NFKC 归一化）
        candidates = db_index.get(base_name.lower(), [])
        # 2. 兜底：数据库可能存的是带扩展名的完整名
        if not candidates:
            candidates = db_index.get(clean.lower(), [])
        if not candidates:
            continue

        # 优先选 file_type 与扩展名一致的；否则取第一个
        chosen = None
        if ext:
            for c in candidates:
                if (c.file_type or "").strip().lower() == ext:
                    chosen = c
                    break
        if not chosen:
            chosen = candidates[0]

        if chosen.id in seen_ids:
            continue
        seen_ids.add(chosen.id)

        full_name = chosen.file_name
        if chosen.file_type and '.' not in full_name:
            full_name = f"{chosen.file_name}.{chosen.file_type}"

        matched_files.append({
            "id": chosen.id,
            "file_name": full_name,
            "file_url": chosen.file_url,
            "file_size": chosen.file_size,
            "file_type": chosen.file_type
        })

    return matched_files


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

        # 分离文件名和扩展名
        base_name, ext = os.path.splitext(uploaded_file.name)
        file_ext = ext.lstrip('.')  # 移除点号，如 "pdf", "docx"
        object_name = f"{uuid.uuid4().hex}{ext}"

        result = upload_file_to_minio(uploaded_file, object_name)

        if result["success"]:
            file_size = uploaded_file.size

            knowledge_file = KnowledgeFile.objects.create(
                file_name=base_name,  # 只保存文件名，不含扩展名
                file_url=result["url"],
                file_size=file_size,
                file_type=file_ext  # 保存扩展名，如 "pdf", "docx"
            )

            saved_records.append({
                "file_name": f"{base_name}{ext}",  # 返回完整文件名供前端显示
                "file_url": result["url"],
                "file_size": file_size,
                "file_type": file_ext,
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

import json
import uuid
import os
import unicodedata
from datetime import datetime
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from file_upload.minio_client import upload_file_to_minio, get_file_from_minio
from .services import call_knowledge_api_streaming, call_knowledge_api_non_streaming, extract_workflow_result, extract_source_files
from .models import KnowledgeFile, Ticket, TicketFile
from api.auth_utils import get_user_from_request


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


# =====================================================================
# 工单系统 API
# =====================================================================

def _serialize_ticket(ticket, include_attachments=True, for_user=None):
    """
    把 Ticket 模型实例转为前端可消费的 dict。
    for_user 用于做字段级权限控制（如 manager_answer 对上报人也可见，
    但 manager_note 仅产品经理/保障人可见）。
    """
    d = {
        "id": ticket.id,
        "question": ticket.question,
        "agent_answer": ticket.agent_answer,
        "reason": ticket.reason,
        "manager_answer": ticket.manager_answer,
        "manager_note": ticket.manager_note,
        "status": ticket.status,
        "status_display": ticket.get_status_display(),
        "reporter_id": ticket.reporter_id,
        "reporter_name": getattr(ticket.reporter, "name", None),
        "reporter_work_id": getattr(ticket.reporter, "work_id", None),
        "handler_id": ticket.handler_id,
        "handler_name": getattr(ticket.handler, "name", None),
        "related_file_id": ticket.related_file_id,
        "related_file_name": ticket.related_file_name,
        "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat(),
    }
    if include_attachments:
        d["attachments"] = [
            {
                "id": a.id,
                "file_name": a.file_name,
                "file_url": a.file_url,
                "file_size": a.file_size,
                "uploaded_at": a.uploaded_at.isoformat(),
            }
            for a in ticket.attachments.all()
        ]
    # manager_note 仅经理/保障人可见
    if for_user and getattr(for_user, "role_id", "") not in ("pm", "guard"):
        d.pop("manager_note", None)
    return d


def _get_current_user(request):
    """优先从 JWT 取用户，失败则尝试 work_id 回退（内部调用无 token 时）。"""
    user = get_user_from_request(request)
    if user is not None:
        return user
    # 兜底：允许通过 query 参数 work_id 定位（开发/内部调用用）
    work_id = request.GET.get("work_id") or request.POST.get("work_id")
    if work_id:
        from api.models import User
        try:
            return User.objects.get(work_id=work_id)
        except User.DoesNotExist:
            return None
    return None


# -------- 1. 创建工单（问题上报） --------

@csrf_exempt
@require_POST
def ticket_create(request):
    """
    POST /api/knowledge/tickets/
    客户经理前端点"问题上报"时调用。

    Request JSON:
        question      (str, 必填) 用户的原始问题
        agent_answer  (str, 可选) 智能体当时给出的回答
        reason        (str, 可选) 用户认为没解决的原因/补充描述
    """
    user = _get_current_user(request)
    if user is None:
        return JsonResponse({"status": "error", "message": "未登录"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "请求体格式错误"}, status=400)

    question = (data.get("question") or "").strip()
    if not question:
        return JsonResponse({"status": "error", "message": "问题内容不能为空"}, status=400)

    ticket = Ticket.objects.create(
        question=question,
        agent_answer=data.get("agent_answer") or "",
        reason=data.get("reason") or "",
        reporter=user,
        status="pending",
    )

    return JsonResponse({
        "status": "success",
        "message": "工单创建成功",
        "data": _serialize_ticket(ticket),
    }, status=201)


# -------- 2. 工单列表 --------

@csrf_exempt
@require_GET
def ticket_list(request):
    """
    GET /api/knowledge/tickets/

    Query params:
        status   筛选状态
        role     "pm"→经理视角看全部 pending/processing/resolved；"gm"→客户经理看自己的
        work_id  兜底（无 token 时）
    """
    user = _get_current_user(request)
    if user is None:
        return JsonResponse({"status": "error", "message": "未登录"}, status=401)

    status = request.GET.get("status")
    role = request.GET.get("role") or getattr(user, "role_id", "")

    qs = Ticket.objects.all()

    if role == "gm":
        # 客户经理：只能看自己上报的
        qs = qs.filter(reporter=user)
    elif role in ("pm", "guard"):
        # 产品经理 / 保障人：看所有未闭环的
        qs = qs.exclude(status="closed")
    else:
        # 默认：看自己上报的
        qs = qs.filter(reporter=user)

    if status:
        qs = qs.filter(status=status)

    tickets = [_serialize_ticket(t, include_attachments=False, for_user=user) for t in qs]
    return JsonResponse({"status": "success", "data": tickets})


# -------- 3. 工单详情 --------

@csrf_exempt
@require_GET
def ticket_detail(request, ticket_id):
    """GET /api/knowledge/tickets/<id>/"""
    user = _get_current_user(request)
    if user is None:
        return JsonResponse({"status": "error", "message": "未登录"}, status=401)

    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return JsonResponse({"status": "error", "message": "工单不存在"}, status=404)

    # 权限：上报人可看自己的，经理/保障人可看所有
    role = getattr(user, "role_id", "")
    if ticket.reporter_id != user.id and role not in ("pm", "guard"):
        return JsonResponse({"status": "error", "message": "无权查看此工单"}, status=403)

    return JsonResponse({
        "status": "success",
        "data": _serialize_ticket(ticket, for_user=user),
    })


# -------- 4. 产品经理：解答工单 --------

@csrf_exempt
@require_POST
def ticket_answer(request, ticket_id):
    """
    POST /api/knowledge/tickets/<id>/answer/
    产品经理填写正式回答。

    Request JSON:
        manager_answer (str, 必填)
        manager_note   (str, 可选，内部备注)
        status         (str, 可选) 默认 "resolved"，也可传 "processing" 先接手不解答
    """
    user = _get_current_user(request)
    if user is None:
        return JsonResponse({"status": "error", "message": "未登录"}, status=401)

    if getattr(user, "role_id", "") not in ("pm", "guard"):
        return JsonResponse({"status": "error", "message": "仅产品经理/保障人可解答工单"}, status=403)

    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return JsonResponse({"status": "error", "message": "工单不存在"}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "请求体格式错误"}, status=400)

    answer = (data.get("manager_answer") or "").strip()
    manager_note = data.get("manager_note") or ""
    new_status = data.get("status") or "resolved"

    if new_status == "resolved" and not answer:
        return JsonResponse({"status": "error", "message": "解答内容不能为空"}, status=400)

    ticket.handler = user
    ticket.manager_answer = answer
    if manager_note:
        ticket.manager_note = manager_note

    if new_status == "processing":
        ticket.status = "processing"
    elif new_status == "resolved":
        ticket.status = "resolved"
        ticket.resolved_at = datetime.now()

    ticket.save()

    return JsonResponse({
        "status": "success",
        "message": "工单已更新",
        "data": _serialize_ticket(ticket, for_user=user),
    })


# -------- 5. 产品经理：闭环（关联知识库条目） --------

@csrf_exempt
@require_POST
def ticket_close(request, ticket_id):
    """
    POST /api/knowledge/tickets/<id>/close/
    产品经理解答后，将工单关联到一条知识库文件，完成闭环。

    Request JSON:
        related_file_id (int, 可选) 已有的 KnowledgeFile.id
        或
        new_file_name   (str, 可选) 想上传到知识库的文件名（走 file_upload 接口）
    """
    user = _get_current_user(request)
    if user is None:
        return JsonResponse({"status": "error", "message": "未登录"}, status=401)

    if getattr(user, "role_id", "") not in ("pm", "guard"):
        return JsonResponse({"status": "error", "message": "仅产品经理/保障人可闭环工单"}, status=403)

    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return JsonResponse({"status": "error", "message": "工单不存在"}, status=404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "请求体格式错误"}, status=400)

    related_file_id = data.get("related_file_id")

    if related_file_id:
        try:
            kf = KnowledgeFile.objects.get(id=related_file_id)
            ticket.related_file = kf
            ticket.related_file_name = f"{kf.file_name}.{kf.file_type}" if kf.file_type else kf.file_name
        except KnowledgeFile.DoesNotExist:
            return JsonResponse({"status": "error", "message": "知识库文件不存在"}, status=404)

    ticket.status = "closed"
    ticket.closed_at = datetime.now()
    # 确保 resolved_at 有值
    if not ticket.resolved_at:
        ticket.resolved_at = datetime.now()
    ticket.save()

    # 通知保障人（复用 api.models.Notification）
    try:
        from api.models import Notification, User
        guards = User.objects.filter(role_id="guard")
        for guard in guards:
            Notification.objects.create(
                title=f"工单 #{ticket.id} 已闭环",
                content=f"问题：{ticket.question[:80]}\n经理：{ticket.handler.name if ticket.handler else '-'}\n已关联知识库：{ticket.related_file_name or '未关联'}",
                level="guard",
                sender=user,
            )
    except Exception:
        pass  # 通知失败不阻塞主流程

    return JsonResponse({
        "status": "success",
        "message": "工单已闭环",
        "data": _serialize_ticket(ticket, for_user=user),
    })


# -------- 6. 工单附件上传 --------

@csrf_exempt
@require_POST
def ticket_upload(request, ticket_id):
    """
    POST /api/knowledge/tickets/<id>/upload/
    为工单追加附件（截图、需求文档等）。

    优先支持 multipart/form-data（文件直传 MinIO），
    也支持 JSON 传 file_url（已上传过的文件复用 URL）。
    """
    user = _get_current_user(request)
    if user is None:
        return JsonResponse({"status": "error", "message": "未登录"}, status=401)

    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        return JsonResponse({"status": "error", "message": "工单不存在"}, status=404)

    saved = []

    # 方式 1：multipart 直传
    if request.FILES:
        for key in ("file", "files", "file[]", "files[]"):
            if key in request.FILES:
                files = request.FILES[key]
                if not isinstance(files, list):
                    files = [files]
                for f in files:
                    if not f.name:
                        continue
                    object_name = f"{uuid.uuid4().hex}{os.path.splitext(f.name)[1]}"
                    result = upload_file_to_minio(f, object_name)
                    if result["success"]:
                        tf = TicketFile.objects.create(
                            ticket=ticket,
                            file_name=f.name,
                            file_url=result["url"],
                            file_size=f.size,
                            uploaded_by=user,
                        )
                        saved.append({"id": tf.id, "file_name": tf.file_name, "file_url": tf.file_url})
                break

    # 方式 2：JSON 传 file_url
    if not saved and request.body:
        try:
            data = json.loads(request.body)
            file_url = data.get("file_url")
            file_name = data.get("file_name") or "attachment"
            if file_url:
                tf = TicketFile.objects.create(
                    ticket=ticket,
                    file_name=file_name,
                    file_url=file_url,
                    file_size=data.get("file_size"),
                    uploaded_by=user,
                )
                saved.append({"id": tf.id, "file_name": tf.file_name, "file_url": tf.file_url})
        except json.JSONDecodeError:
            pass

    if not saved:
        return JsonResponse({"status": "error", "message": "未收到可上传的文件"}, status=400)

    return JsonResponse({
        "status": "success",
        "message": f"上传 {len(saved)} 个附件",
        "data": saved,
    })


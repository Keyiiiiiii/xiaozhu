import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .services import call_knowledge_api_streaming, call_knowledge_api_non_streaming, extract_workflow_result


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
import os
import unicodedata
import requests
import json
import re
from django.conf import settings


def call_knowledge_api_streaming(
    question: str,
    user_id: str = "",
    app_id: str = "",
    workflow_id: str = "",
    workflow_run_id: str = ""
):
    headers = {
        "Authorization": f"Bearer {settings.KNOWLEDGE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": {"ques": question},
        "response_mode": "streaming",
        "user": user_id or "abc-123"
    }
    
    try:
        response = requests.post(
            settings.KNOWLEDGE_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=300
        )
        
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                yield line.decode("utf-8")
                
    except requests.exceptions.Timeout:
        raise Exception("请求超时")
    except requests.exceptions.ConnectionError:
        raise Exception("无法连接到 API 服务器")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP 错误: {e}")
    except Exception as e:
        raise Exception(f"未知错误: {e}")


def call_knowledge_api_non_streaming(
    question: str,
    user_id: str = "",
    app_id: str = "",
    workflow_id: str = "",
    workflow_run_id: str = ""
):
    headers = {
        "Authorization": f"Bearer {settings.KNOWLEDGE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": {"ques": question},
        "response_mode": "blocking",
        "user": user_id or "abc-123"
    }
    
    try:
        response = requests.post(
            settings.KNOWLEDGE_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=300
        )
        
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                full_response += line.decode("utf-8")
        
        return extract_workflow_result(full_response)
                
    except requests.exceptions.Timeout:
        raise Exception("请求超时")
    except requests.exceptions.ConnectionError:
        raise Exception("无法连接到 API 服务器")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP 错误: {e}")
    except Exception as e:
        raise Exception(f"未知错误: {e}")


def extract_workflow_result(stream_output: str) -> dict:
    """
    从工作流响应中提取最终结果。

    实测响应格式（berry-apps 平台 streaming 模式实际返回的是单行 JSON，
    不是标准 SSE）：
        {
          "data": {
            "task_id": "...",
            "data": {
              "outputs": {
                "text": "LLM 回复正文（可能含一行错误的'原文件标题：xxx'）",
                "result": [
                  {"text": "...", "metadata": {"file_name": "榕小助/弱电系统按建筑功能分类介绍.docx"}},
                  ...
                ]
              }
            }
          }
        }

    提取逻辑：
      - content  : outputs.text（删除 LLM 自造的"原文件标题：xxx"那行）
      - source_files : 遍历 result[].metadata.file_name，取 basename 去扩展名
                       例如 "榕小助/弱电系统按建筑功能分类介绍.docx" → "弱电系统按建筑功能分类介绍"
    """
    if not stream_output:
        return {"content": "响应内容为空", "source_files": []}

    root_obj = None

    # 1. 优先直接 JSON 解析（实际响应就是单个 JSON 对象）
    try:
        root_obj = json.loads(stream_output)
    except json.JSONDecodeError:
        root_obj = None

    # 2. 兜底：按 SSE 格式拆分（兼容真正的流式返回）
    if not isinstance(root_obj, dict):
        pattern = r'data:\s*({.*?})(?=data:|$)'
        data_lines = [m.strip() for m in re.findall(pattern, stream_output, re.DOTALL) if m.strip()]
        for content in data_lines:
            try:
                content = re.sub(r",\s*}", "}", content)
                content = re.sub(r",\s*]", "]", content)
                content = content.replace("，", ",")
                obj = json.loads(content)
                if obj.get("event") == "workflow_finished" or isinstance(obj.get("data"), dict):
                    root_obj = obj
                    break
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

    if not isinstance(root_obj, dict):
        return {"content": stream_output[:2000], "source_files": []}

    # 3. 定位 outputs，兼容多种嵌套：
    #    - root.data.data.outputs.result  (berry-apps 包装层)
    #    - root.data.outputs.result      (workflow_finished 事件)
    #    - root.outputs.result           (直接)
    outputs = None
    data_layer = root_obj.get("data")
    if isinstance(data_layer, dict):
        inner_data = data_layer.get("data")
        if isinstance(inner_data, dict):
            outputs = inner_data.get("outputs") or data_layer.get("outputs")
        if not outputs:
            outputs = data_layer.get("outputs")
    if not outputs:
        outputs = root_obj.get("outputs")

    if not isinstance(outputs, dict):
        return {"content": stream_output[:2000], "source_files": []}

    # 4. 提取 result 数组（可能是 JSON 字符串或已是 list）
    result_raw = outputs.get("result")
    result_array = None
    if isinstance(result_raw, str):
        try:
            result_array = json.loads(result_raw)
        except json.JSONDecodeError:
            result_array = None
    elif isinstance(result_raw, list):
        result_array = result_raw

    # 5. content 优先用 outputs.text（LLM 总结回复）
    content = outputs.get("text", "") or outputs.get("answer", "") or ""
    if not content and isinstance(result_array, list):
        parts = []
        for item in result_array:
            if isinstance(item, dict):
                t = item.get("text") or item.get("content") or ""
                if t and isinstance(t, str):
                    parts.append(t.strip())
        content = "\n\n".join(parts)
    if not content:
        content = stream_output[:2000]

    # 6. 删除 LLM 在 text 末尾自造的"原文件标题：xxx"那行
    #    （这行标题是 LLM 瞎编的，真正源文件名要从 metadata.file_name 提取）
    content = re.sub(
        r'[ \t]*\n*[ \t]*\**\s*原文件标题\s*[#：:]\s*[^\n]*',
        '',
        content
    )
    content = content.rstrip()

    # 7. 从 result 数组的 metadata.file_name 提取 source_files
    #    "榕小助/弱电系统按建筑功能分类介绍.docx" → "弱电系统按建筑功能分类介绍"
    source_files = []
    seen = set()
    if isinstance(result_array, list):
        for item in result_array:
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata") or {}
            file_name_raw = metadata.get("file_name") or item.get("file_name")
            if not (file_name_raw and isinstance(file_name_raw, str)):
                continue
            base = os.path.basename(file_name_raw.replace("\\", "/"))
            display_name, _ = os.path.splitext(base)
            # NFKC 归一化：把兼容性字符转为标准形式（如 U+2F34 → U+5E7F）
            display_name = unicodedata.normalize('NFKC', display_name.strip())
            if display_name and display_name not in seen:
                seen.add(display_name)
                source_files.append(display_name)

    return {"content": content, "source_files": source_files}


def extract_source_files(text_content: str) -> list:
    """
    保留旧接口签名以避免外部引用报错。
    实际逻辑已由 extract_workflow_result 内部直接从 metadata.file_name 提取，
    这里仅做兜底：从文本中匹配 "原文件标题:" 等标签。
    """
    source_files = []
    title_patterns = [
        r'\*\*原文件标题\*\*[#：:]\s*(.+)',
        r'原文件标题[#：:]\s*(.+)',
        r'源文件[#：:]\s*(.+)',
        r'参考文件[#：:]\s*(.+)',
    ]
    for pattern in title_patterns:
        for match in re.findall(pattern, text_content):
            source_files.append(match.strip())
    return source_files
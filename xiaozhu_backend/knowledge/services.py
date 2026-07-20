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
    if not stream_output:
        return {"content": "响应内容为空"}
    
    text_patterns = [
        r'"text"\s*[:：]\s*["“](.*?)["”](?=\s*[,，}\)\]])',
        r"text\s*[:：]\s*[\"“](.*?)[\"”](?=\s*[,，}\)\]])",
        r'"text"\s*[:：]\s*(.+?)(?=\s*["”])',
    ]
    
    for pattern in text_patterns:
        matches = re.findall(pattern, stream_output, re.DOTALL)
        if matches:
            text_content = matches[0].strip()
            if text_content:
                return {"content": text_content}
    
    data_patterns = [
        r'"data"\s*[:：]\s*\(\s*\{(.*?)\}\s*\)',
        r'"data"\s*[:：]\s*\((.*?)\)',
    ]
    
    for pattern in data_patterns:
        matches = re.findall(pattern, stream_output, re.DOTALL)
        if matches:
            inner_content = matches[0].strip()
            for text_pattern in text_patterns:
                text_matches = re.findall(text_pattern, inner_content, re.DOTALL)
                if text_matches:
                    text_content = text_matches[0].strip()
                    if text_content:
                        return {"content": text_content}
    
    chinese_pattern = r'[\u4e00-\u9fff]+[^\u4e00-\u9fff]*[\u4e00-\u9fff]+'
    chinese_matches = re.findall(chinese_pattern, stream_output)
    if chinese_matches:
        return {"content": "".join(chinese_matches[:50])}
    
    return {"content": stream_output[:2000]}
import requests
import json
import time
from typing import Optional, Dict, Any
import re
import pandas as pd


# API 配置信息
API_URL = "http://36.212.132.154:30086/berry-apps/server/apps/api"
API_KEY = "GtjGSJ2V4rrQP-rg457sbi3BDJM7vyDv"  # 替换为你的真实 API Key
USER_ID = "abc-123"  # 可根据需要修改用户标识


def extract_workflow_final_result(stream_output: str) -> dict:
    """
    从工作流流式输出中提取最终结果（兼容JSON格式异常/无workflow_finished事件）
    
    Args:
        stream_output: 完整的流式输出文本（所有行拼接的字符串）
    
    Returns:
        解析后的最终结果字典
    """
    # 1. 修正：正确拆分data:开头的JSON片段（核心修复）
    # 匹配所有以data:开头，下一个data:之前的内容（处理连续拼接的情况）
    pattern = r'data:\s*({.*?})(?=data:|$)'
    matches = re.findall(pattern, stream_output, re.DOTALL)  # re.DOTALL让.匹配换行符
    data_lines = [match.strip() for match in matches if match.strip()]

    if not data_lines:
        raise ValueError("未提取到任何data:开头的JSON片段！")

    # 2. 尝试解析每一行，优先找workflow_finished
    final_result = None
    
    for idx, content in enumerate(data_lines):
        try:
            # 修复常见的JSON格式问题
            content = re.sub(r",\s*}", "}", content)  # 去掉末尾多余逗号
            content = re.sub(r",\s*]", "]", content)
            # 替换中文逗号为英文逗号（关键修复：处理中文标点）
            content = re.sub(r"，", ",", content)
            data_obj = json.loads(content)
            
            if data_obj.get("event") == "workflow_finished":
                result_str = data_obj["data"]["outputs"]["result"]
                # 清理结果字符串中的多余空格/换行（鲁棒性优化）
                result_str = re.sub(r'\s+', ' ', result_str).strip()
                final_result = json.loads(result_str)
                print(f"✅ 从workflow_finished事件提取结果成功")
                break
            
                
        
        except json.JSONDecodeError as e:
            print(f"❌ 第{idx+1}行JSON解析失败: {e}，跳过该行")
            continue
        except KeyError as e:
            print(f"❌ 第{idx+1}行缺失字段: {e}，跳过该行")
            continue
    
    # 最终结果优先级：workflow_finished > LLM节点结果
    final_result = final_result
    if not final_result:
        raise ValueError(
            "未找到有效结果！\n"
            "可能原因：1. 工作流未执行完（无workflow_finished）；2. 无LLM节点输出；3. 所有行JSON格式错误"
        )
    
    return final_result


def test_api(
    inputs: Dict[str, Any] = None,
    response_mode: str = "streaming",
    user: str = USER_ID,
    files: Optional[list] = None
) -> None:
    """
    测试 API 接口的函数
    
    参数:
        inputs: 传入的变量键值对，默认为空字典
        response_mode: 响应模式，支持 "streaming" 或 "blocking"
        user: 用户唯一标识
        files: 文件列表（图片），适用于支持 Vision 能力的模型
    """
    # 设置默认值
    if inputs is None:
        inputs = {}
    
    # 构建请求头
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建请求体
    payload = {
        "inputs": inputs,
        "response_mode": response_mode,  # 注意接口字段是 response_mode
        "user": user
    }
    
    # 如果有文件参数，添加到请求体
    if files:
        payload["files"] = files
    
    try:
        print(f"开始请求 API，响应模式：{response_mode}")
        print(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        print("-" * 50)
        
        start_time = time.time()
        
        # 根据响应模式处理请求
        if response_mode == "streaming":
            # 流式响应处理（SSE）
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                stream=False,
                timeout=300  # 流式响应超时时间设为 5 分钟
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 逐行读取流式响应
            full_response = ""
            for line in response.iter_lines():
                if line:
                    # 解码并处理每行数据
                    line_data = line.decode("utf-8")
                    full_response = full_response + line_data
                    print(f"流式返回: {line_data}")
            
            print("-" * 50)
            print(f"流式响应接收完成，总长度: {len(full_response)} 字符")
            #print(full_response)
            final_result = extract_workflow_final_result(full_response)
        
        else:
            # 阻塞模式响应处理
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=100  # 阻塞模式按接口要求设为 100 秒
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析 JSON 响应
            result = response.json()
            print(f"为按成阻塞模式处理，阻塞返回: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return None
        
        # 输出请求耗时
        elapsed_time = time.time() - start_time
        print(f"\n请求成功完成，耗时: {elapsed_time:.2f} 秒")
        print(f"响应状态码: {response.status_code}")
        return final_result
    except requests.exceptions.Timeout:
        print(f"\n错误：请求超时（{response_mode} 模式）")
        return None
    except requests.exceptions.ConnectionError:
        print("\n错误：无法连接到 API 服务器，请检查网络或 URL")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP 错误: {e}")
        print(f"响应内容: {response.text if 'response' in locals() else '无'}")
        return None
    except Exception as e:
        print(f"\n未知错误: {type(e).__name__} - {e}")
        return None

if __name__ == "__main__":
    # ========== 测试示例 ==========
    # 1. 测试流式模式（默认）
    
    result_json = test_api(
        inputs={
            "ques":"联想百应适合解决什么问题？"
       },  # 可根据需要添加变量，例如：{"question": "你好", "context": "测试上下文"}
        response_mode="streaming",
        user="abc-123"
    )
    



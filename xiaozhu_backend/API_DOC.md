# 榕小助后端 API 接口文档

### 配置路径 xiaozhu/xiaozhu_backend/xiaozhu_backend/settings.py
```bash
# mac 启动流程：
# 0、安装minio，建立bucket “xiaozhu”
# 1、终端启动minio服务：
minio server ~/minio-data --console-address ":9001"
# 账号密码：minioadmin/minioadmin
# 2、启动django后端：
source .venv/bin/activate
cd /xiaozhu/xiaozhu_backend
python manage.py runserver
# 3、请求后端接口：
curl -X POST http://localhost:8000/api/file/upload/ \
  -F "file=@test.m4a" \
  -F "creator_id=1" \      
  -F "customer_name=张三" \   
  -F "visit_time=2026-07-17" \
  -F "status=1"

curl -X POST http://localhost:8000/api/file/speech-to-text/ -d "creator_id=1" -d "id=1"
```

## 基础信息

- **服务地址**: `http://localhost:8000`
- **API 前缀**: `/api/file`
- **Content-Type**: `multipart/form-data` 或 `application/x-www-form-urlencoded`

---

## 1. 文件上传接口

### 接口描述

上传音频文件到 MinIO 存储，同时在数据库 `api_visitrecord` 表中创建走访记录，并返回文件访问 URL。

### 请求信息

- **URL**: `POST /api/file/upload/`
- **Method**: `POST`

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `file` | File | 是 | - | 音频文件，支持字段名：`file`、`files`、`file[]`、`files[]` |
| `creator_id` | Integer | 否 | `1` | 创建人ID，需对应 `api_user` 表中存在的用户 |
| `customer_name` | String | 否 | `"cus"` | 走访对象名称 |
| `visit_time` | String | 否 | `"2026-07-01"` | 走访时间，格式：`YYYY-MM-DD` |
| `status` | Integer | 否 | `1` | 状态值，映射关系见下表 |

### 状态值映射

| 数字值 | 字符串值 | 说明 |
| :--- | :--- | :--- |
| `1` | `pending` | 等待处理 |
| `2` | `processing` | 处理中 |
| `3` | `success` | 处理成功 |
| `4` | `failed` | 处理失败 |

### 支持的文件格式

- `.m4a`
- `.mp3`
- `.wav`
- `.ogg`
- `.flac`

### 成功响应

**Status Code**: `200 OK`

```json
{
    "status": "success",
    "message": "文件上传成功",
    "file_url": "http://localhost:9000/xiaozhu/da16a319bd1949a783be18783b8fbf9f.m4a",
    "record_id": 1
}
```

### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "没有找到文件，接收到的字段: []"
}
```

```json
{
    "status": "error",
    "message": "用户ID 1 不存在"
}
```

**Status Code**: `500 Internal Server Error`

```json
{
    "status": "error",
    "message": "文件上传失败: S3Error: ..."
}
```

### 示例请求

```bash
curl -X POST http://localhost:8000/api/file/upload/ \
  -F "file=@test.m4a" \
  -F "creator_id=1" \
  -F "customer_name=张三" \
  -F "visit_time=2026-07-17" \
  -F "status=1"
```

### 数据库记录

上传成功后，会在 `api_visitrecord` 表中创建一条记录：

| 字段 | 说明 |
| :--- | :--- |
| `creator_id` | 创建人ID，关联 `api_user` 表 |
| `customer_name` | 走访对象名称 |
| `audio_url` | MinIO 文件访问 URL |
| `visit_time` | 走访时间 |
| `status` | 处理状态 |

---

## 2. 语音转文字接口

### 接口描述

根据 `creator_id` 和 `id` 从数据库 `api_visitrecord` 表中获取对应的音频文件 URL，调用外部语音转文字 API 进行转写，将转写结果存入 `original_text` 字段并更新状态。

### 请求信息

- **URL**: `POST /api/file/speech-to-text/`
- **Method**: `POST`

### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `creator_id` | Integer | 否 | `1` | 创建人ID，需对应 `api_user` 表中存在的用户 |
| `id` | Integer | 否 | `1` | 走访记录ID，需对应 `api_visitrecord` 表中存在的记录 |

### 成功响应

**Status Code**: `200 OK`

```json
{
    "status": "success", 
    "data": {
        "job_id": "3b97f597455c4296b98861d8f0225196", 
        "status": "done", 
        "progress": 100, 
        "message": "Done", 
        "segments": [
            {"start": 0.0, 
            "end": 2.58, 
            "text": "\u6211\u79fb......", 
            "speaker_label": "speaker_2", 
            "confidence": 0.688440835154609, 
            "speaker_confidence": null}, 
            {...}
        ],
         "error": null, 
         "elapsed_seconds": 65.0, 
         "created_at": "2026-07-17T03:16:01", 
         "updated_at": "2026-07-17T03:17:06"
    }
}
```

### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "走访记录 ID=1, creator_id=1 不存在"
}
```

```json
{
    "status": "error",
    "message": "该走访记录没有关联的音频文件URL"
}
```

**Status Code**: `500 Internal Server Error`

```json
{
    "status": "error",
    "message": "从MinIO获取文件失败: S3Error: ..."
}
```

```json
{
    "status": "error",
    "message": "转写失败: {...}"
}
```

```json
{
    "status": "error",
    "message": "调用语音转文字API失败: ConnectionError: ..."
}
```

### 示例请求

```bash
curl -X POST http://localhost:8000/api/file/speech-to-text/ \
  -d "creator_id=1" \
  -d "id=1"
```

### 数据库更新

转写完成后，会更新 `api_visitrecord` 表中对应记录：

| 字段 | 更新逻辑 |
| :--- | :--- |
| `original_text` | 存入语音转写结果（`segments` 字段内容） |
| `status` | 根据转写状态更新：`processing` → `success` / `failed` |

---

## 接口调用流程

```
客户端上传文件 → 创建走访记录 → 调用语音转文字接口 → 获取转写结果
    ↓                    ↓                      ↓
POST /upload/         DB记录               POST /speech-to-text/
    ↓              (creator_id,              (creator_id, id)
 上传到MinIO        id, audio_url)              ↓
    ↓                                          ↓
 创建VisitRecord                           查询DB获取audio_url
 (含MinIO URL)                                  ↓
                                              从MinIO下载文件
                                                 ↓
                                              调用外部ASR API
                                              创建任务 → 轮询状态 → 删除任务
                                                    ↓
                                              更新DB: original_text + status
                                                    ↓
                                              返回转写结果
```

---

## 错误码说明

| HTTP 状态码 | 说明 |
| :--- | :--- |
| `400` | 请求参数错误（文件不存在、file_url为空等） |
| `500` | 服务器内部错误（MinIO操作失败、API调用失败等） |

# 榕小助后端 API 接口文档

## 首次环境（零数据必做）

```bash
cd xiaozhu_backend
pip install -r ../requirements.txt
python manage.py makemigrations api
python manage.py migrate
python manage.py seed_test_users   # 写入测试账号，可重复执行
daphne xiaozhu_backend.asgi:application -b 0.0.0.0 -p 8000
```

**测试账号**（`seed_test_users` 写入）：


| 工号        | 密码       | 说明     |
| --------- | -------- | ------ |
| `admin`   | `123456` | 默认联调账号 |
| `FZ10086` | `123456` | 第二测试用户 |


业务接口（`/api/file/*`）需在请求头携带 JWT：`Authorization: Bearer <access_token>`。用户身份由 token 解析，**无需**再传 `creator_id`。

---

## 认证接口（`/api/auth`）

### 1. 登录

- **URL**: `POST /api/auth/login/`
- **Body (JSON)**: `{"username": "admin", "password": "123456"}`（`username` 支持工号或用户名）

**成功响应**:

```json
{
  "status": "success",
  "message": "登录成功",
  "data": {
    "token": "<access_jwt>",
    "refresh": "<refresh_jwt>",
    "userInfo": {
      "id": 2,
      "username": "admin",
      "name": "张三",
      "role": "客户经理",
      "dept": "市公司 / 政企客户部 / 第一网格",
      "empId": "admin"
    }
  }
}
```



### 2. 当前用户（认证 / 验 token）

- **URL**: `GET /api/auth/me/`
- **Header**: `Authorization: Bearer <access_token>`



### 3. 刷新 Token

- **URL**: `POST /api/auth/refresh/`
- **Body (JSON)**: `{"refresh": "<refresh_jwt>"}`



### 4. 登出

- **URL**: `POST /api/auth/logout/`
- MVP 以前端清除本地 token 为主；接口返回成功即可。

---



### 配置路径 xiaozhu/xiaozhu_backend/xiaozhu_backend/settings.py

```bash
# mac 启动流程：
# 0、安装minio，建立bucket "xiaozhu"
# 1、终端启动minio服务：
minio server ~/minio-data --console-address ":9001"
# 账号密码：minioadmin/minioadmin
# 2、安装Redis（首次使用）：
brew install redis
/opt/homebrew/opt/redis/bin/redis-server /opt/homebrew/etc/redis.conf --daemonize yes
# 3、启动django后端（使用daphne支持WebSocket）：
source .venv/bin/activate
cd /xiaozhu/xiaozhu_backend
daphne xiaozhu_backend.asgi:application -b 0.0.0.0 -p 8000
# 4、先登录获取 token，再请求业务接口（需 Header: Authorization: Bearer <token>）：
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")

curl -X POST http://localhost:8000/api/file/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.m4a" \
  -F "customer_name=张三" \
  -F "visit_time=2026-07-17" \
  -F "status=1" \
  -F "duration_seconds=10"

curl -X POST http://localhost:8000/api/file/speech-to-text/ \
  -H "Authorization: Bearer $TOKEN" -d "id=1"

curl -X POST http://localhost:8000/api/file/summarize/ \
  -H "Authorization: Bearer $TOKEN" -d "id=1"

curl -X POST http://localhost:8000/api/file/record-ids/ \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8000/api/file/record-detail/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1"

curl -X POST http://localhost:8000/api/file/update-original-text/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=10" \
  -d "original_text=新的转写文本内容..." \
  -d "visit_time=2026-04-01" \
  -d "customer_name=test张"

curl -X POST http://localhost:8000/api/file/delete-record/ \
  -H "Authorization: Bearer $TOKEN" -d "id=1"

curl -X POST http://localhost:8000/api/file/get-audio-file/ \
  -H "Authorization: Bearer $TOKEN" -d "id=1"

# 5、WebSocket连接获取转写结果：
ws://localhost:8000/ws/asr/{job_id}/
```



## 基础信息

- **服务地址**: `http://localhost:8000`
- **API 前缀**: `/api/file`
- **Content-Type**: `multipart/form-data` 或 `application/x-www-form-urlencoded`
- **WebSocket 前缀**: `ws://localhost:8000/ws/asr`



### 业务接口鉴权

- **Header**: `Authorization: Bearer <access_token>`（先调用 `POST /api/auth/login/` 获取 token）
- 用户身份由 JWT 解析，**不要**在请求体中传 `creator_id`
- 未带或无效 token → `401`，`message`: `未登录或 token 无效`

---



## 1. 文件上传接口



### 接口描述

上传音频文件到 MinIO 存储，同时计算文件时长并在数据库 `api_visitrecord` 表中创建走访记录，返回文件访问 URL。

### 请求信息

- **URL**: `POST /api/file/upload/`
- **Method**: `POST`



### 请求参数


| 参数名                | 类型      | 必填  | 默认值            | 说明                                           |
| ------------------ | ------- | --- | -------------- | -------------------------------------------- |
| `Authorization`    | Header  | 是   | -              | `Bearer <access_token>`                      |
| `file`             | File    | 是   | -              | 音频文件，支持字段名：`file`、`files`、`file[]`、`files[]` |
| `customer_name`    | String  | 否   | `"cus"`        | 走访对象名称                                       |
| `visit_time`       | String  | 否   | `"2026-07-01"` | 走访时间，格式：`YYYY-MM-DD`                         |
| `status`           | Integer | 否   | `1`            | 状态值，映射关系见下表                                  |
| `duration_seconds` | Integer | 否   | `0`            | 音频时长，单位：秒                                    |




### 状态值映射


| 数字值 | 字符串值         | 说明   |
| --- | ------------ | ---- |
| `1` | `pending`    | 等待处理 |
| `2` | `processing` | 处理中  |
| `3` | `success`    | 处理成功 |
| `4` | `failed`     | 处理失败 |




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
    "record_id": 1,
    "duration_seconds": 120
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
    "message": "未登录或 token 无效"
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
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.m4a" \
  -F "customer_name=张三" \
  -F "visit_time=2026-07-17" \
  -F "status=1"
```



### 数据库记录

上传成功后，会在 `api_visitrecord` 表中创建一条记录：


| 字段              | 说明                    |
| --------------- | --------------------- |
| `creator_id`    | 创建人ID，关联 `api_user` 表 |
| `customer_name` | 走访对象名称                |
| `audio_url`     | MinIO 文件访问 URL        |
| `visit_time`    | 走访时间                  |
| `status`        | 处理状态                  |


---



## 2. 语音转文字接口（异步模式）



### 接口描述

根据登录用户与记录 `id` 从数据库 `api_visitrecord` 表中获取对应的音频文件 URL，调用外部语音转文字 API 进行转写。**接口为异步模式**，提交任务后立即返回 `job_id`，转写结果通过 WebSocket 推送。

### 请求信息

- **URL**: `POST /api/file/speech-to-text/`
- **Method**: `POST`



### 请求参数


| 参数名             | 类型      | 必填  | 默认值 | 说明                      |
| --------------- | ------- | --- | --- | ----------------------- |
| `Authorization` | Header  | 是   | -   | `Bearer <access_token>` |
| `id`            | Integer | 是   | -   | 走访记录ID，需属于当前登录用户        |




### 成功响应

**Status Code**: `200 OK`

```json
{
    "status": "success",
    "message": "转写任务已提交",
    "job_id": "3b97f597455c4296b98861d8f0225196",
    "record_id": 1
}
```



### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "走访记录 ID=1 不存在"
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
    "message": "调用语音转文字API失败: ConnectionError: ..."
}
```



### 示例请求

```bash
curl -X POST http://localhost:8000/api/file/speech-to-text/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1"
```



### 数据库更新

转写过程中及完成后，会更新 `api_visitrecord` 表中对应记录：


| 字段              | 更新逻辑                                                       |
| --------------- | ---------------------------------------------------------- |
| `status`        | `pending` → `processing`（提交任务时）→ `success` / `failed`（完成时） |
| `original_text` | 转写成功后存入语音转写结果（`segments` 字段内容）                             |


---



## 3. WebSocket 转写结果推送接口



### 接口描述

通过 WebSocket 连接接收语音转写结果。前端提交转写任务获取 `job_id` 后，建立 WebSocket 连接等待结果推送。

### 连接信息

- **URL**: `ws://localhost:8000/ws/asr/{job_id}/`
- **Protocol**: `WebSocket`



### 连接流程

1. 调用 `POST /api/file/speech-to-text/` 获取 `job_id`
2. 使用 `job_id` 建立 WebSocket 连接
3. 等待服务端推送转写结果
4. 结果推送完成后，服务端主动关闭连接



### 推送消息格式

**转写成功**:

```json
{
    "status": "success",
    "data": {
        "job_id": "3b97f597455c4296b98861d8f0225196",
        "status": "done",
        "progress": 100,
        "message": "Done",
        "segments": [
            {
                "start": 0.0,
                "end": 2.58,
                "text": "你好...",
                "speaker_label": "speaker_2",
                "confidence": 0.688,
                "speaker_confidence": null
            }
        ],
        "error": null,
        "elapsed_seconds": 65.0,
        "created_at": "2026-07-17T03:16:01",
        "updated_at": "2026-07-17T03:17:06"
    }
}
```

**转写失败**:

```json
{
    "status": "error",
    "message": "转写失败: {...}"
}
```

**转写超时**:

```json
{
    "status": "error",
    "message": "转写超时: 超过 600 秒"
}
```



### 示例代码

**JavaScript**:

```javascript
// 提交转写任务
const response = await fetch('/api/file/speech-to-text/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Bearer ${token}`
    },
    body: 'id=1'
});
const result = await response.json();
const jobId = result.job_id;

// 建立WebSocket连接
const ws = new WebSocket(`ws://localhost:8000/ws/asr/${jobId}/`);

ws.onopen = () => {
    console.log('WebSocket 连接已建立');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.status === 'success') {
        console.log('转写成功:', data.data);
    } else {
        console.error('转写失败:', data.message);
    }
};

ws.onclose = (event) => {
    console.log('WebSocket 连接已关闭');
};

ws.onerror = (error) => {
    console.error('WebSocket 连接错误:', error);
};
```

**Python**:

```python
import asyncio
import websockets
import json

async def get_asr_result(job_id):
    async with websockets.connect(f'ws://localhost:8000/ws/asr/{job_id}/') as ws:
        print(f'WebSocket 连接已建立: ws://localhost:8000/ws/asr/{job_id}/')
        message = await ws.recv()
        data = json.loads(message)
        print('转写结果:', json.dumps(data, ensure_ascii=False, indent=2))

asyncio.run(get_asr_result('your_job_id_here'))
```

---



## 4. 录音内容总结接口



### 接口描述

根据 `record_id`（id）从数据库 `api_visitrecord` 表中获取 `original_text` 字段内容，调用 AI 总结接口进行总结，并将总结结果存入 `ai_summary` 字段。

### 请求信息

- **URL**: `POST /api/file/summarize/`
- **Method**: `POST`



### 请求参数


| 参数名             | 类型      | 必填  | 默认值 | 说明                      |
| --------------- | ------- | --- | --- | ----------------------- |
| `Authorization` | Header  | 是   | -   | `Bearer <access_token>` |
| `id`            | Integer | 是   | -   | 走访记录ID，需属于当前登录用户        |




### 成功响应

**Status Code**: `200 OK`

```json
{
    "status": "success",
    "message": "总结成功",
    "ai_summary": "总结内容...",
    "record_id": 1
}
```



### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "id 不能为空"
}
```

```json
{
    "status": "error",
    "message": "走访记录 ID=1 不存在"
}
```

```json
{
    "status": "error",
    "message": "原始转写文本为空，无法进行总结"
}
```

**Status Code**: `500 Internal Server Error`

```json
{
    "status": "error",
    "message": "调用总结API失败: ConnectionError: ..."
}
```

```json
{
    "status": "error",
    "message": "总结API响应格式错误: data"
}
```



### 示例请求

```bash
curl -X POST http://localhost:8000/api/file/summarize/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1"
```



### 数据库更新

总结成功后，会更新 `api_visitrecord` 表中对应记录：


| 字段           | 更新逻辑       |
| ------------ | ---------- |
| `ai_summary` | 存入 AI 总结结果 |


---



## 5. 获取记录ID列表接口



### 接口描述

根据登录用户从数据库 `api_visitrecord` 表中获取该用户下所有走访记录的 ID 列表。

### 请求信息

- **URL**: `POST /api/file/record-ids/`
- **Method**: `POST`



### 请求参数


| 参数名             | 类型     | 必填  | 默认值 | 说明                      |
| --------------- | ------ | --- | --- | ----------------------- |
| `Authorization` | Header | 是   | -   | `Bearer <access_token>` |




### 成功响应

**Status Code**: `200 OK`

```json
{
    "status": "success",
    "message": "获取成功",
    "records": [
        [1, "success", "张三", 120, "2026-07-20T10:30:00"],
        [2, "pending", "李四", 60, "2026-07-21T14:15:00"]
    ]
}
```

响应数据结构说明：


| 索引  | 字段名              | 类型           | 说明          |
| --- | ---------------- | ------------ | ----------- |
| 0   | id               | Integer      | 走访记录ID      |
| 1   | status           | String       | 处理状态        |
| 2   | customer_name    | String       | 走访对象名称      |
| 3   | duration_seconds | Integer/null | 音频时长（秒）     |
| 4   | visit_time       | String/null  | 走访时间（ISO格式） |




### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "未登录或 token 无效"
}
```



### 示例请求

```bash
curl -X POST http://localhost:8000/api/file/record-ids/ \
  -H "Authorization: Bearer $TOKEN"
```

---



## 6. 获取记录详情接口



### 接口描述

根据登录用户与记录 `id` 从数据库 `api_visitrecord` 表中获取完整的走访记录信息。

### 请求信息

- **URL**: `POST /api/file/record-detail/`
- **Method**: `POST`



### 请求参数


| 参数名             | 类型      | 必填  | 默认值 | 说明                      |
| --------------- | ------- | --- | --- | ----------------------- |
| `Authorization` | Header  | 是   | -   | `Bearer <access_token>` |
| `id`            | Integer | 是   | -   | 走访记录ID，需属于当前登录用户        |




### 成功响应

**Status Code**: `200 OK`

```json
{
    "status": "success",
    "message": "获取成功",
    "data": {
        "id": 1,
        "creator_id": 1,
        "customer_name": "张三",
        "audio_url": "http://localhost:9000/xiaozhu/xxx.m4a",
        "original_text": "[{'start': 0.0, 'end': 2.58, 'text': '你好...', ...}]",
        "ai_summary": "总结内容...",
        "visit_time": "2026-07-20T10:30:00",
        "duration_seconds": 120,
        "business_type": null,
        "status": "success"
    }
}
```



### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "id 不能为空"
}
```

```json
{
    "status": "error",
    "message": "走访记录 ID=1 不存在"
}
```



### 示例请求

```bash
curl -X POST http://localhost:8000/api/file/record-detail/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1"
```

---



## 7. 更新录音文本接口



### 接口描述

根据登录用户与记录 `id` 更新数据库 `api_visitrecord` 表中对应记录的 `original_text`、`customer_name` 和 `visit_time` 字段。支持按需更新，至少传入一个可更新字段。

### 请求信息

- **URL**: `POST /api/file/update-original-text/`
- **Method**: `POST`



### 请求参数


| 参数名             | 类型      | 必填  | 默认值 | 说明                       |
| --------------- | ------- | --- | --- | ------------------------ |
| `Authorization` | Header  | 是   | -   | `Bearer <access_token>`  |
| `id`            | Integer | 是   | -   | 走访记录ID，需属于当前登录用户         |
| `original_text` | String  | 否   | -   | 更新后的录音转写文本内容             |
| `customer_name` | String  | 否   | -   | 更新后的走访对象名称               |
| `visit_time`    | String  | 否   | -   | 更新后的走访时间，格式：`YYYY-MM-DD` |




### 成功响应

**Status Code**: `200 OK`

```json
{
    "status": "success",
    "message": "更新成功",
    "record_id": 1
}
```



### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "id 不能为空"
}
```

```json
{
    "status": "error",
    "message": "original_text、customer_name、visit_time 至少传一个"
}
```

```json
{
    "status": "error",
    "message": "visit_time 格式错误，应为 YYYY-MM-DD"
}
```

```json
{
    "status": "error",
    "message": "走访记录 ID=1 不存在"
}
```



### 示例请求

更新录音文本：

```bash
curl -X POST http://localhost:8000/api/file/update-original-text/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1" \
  -d "original_text=新的转写文本内容..."
```

更新走访对象和时间：

```bash
curl -X POST http://localhost:8000/api/file/update-original-text/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1" \
  -d "customer_name=新客户" \
  -d "visit_time=2026-08-01"
```



### 数据库更新

更新成功后，会更新 `api_visitrecord` 表中对应记录：


| 字段              | 更新逻辑                  |
| --------------- | --------------------- |
| `original_text` | 更新为传入的录音转写文本内容（仅当传入时） |
| `customer_name` | 更新为传入的走访对象名称（仅当传入时）   |
| `visit_time`    | 更新为传入的走访时间（仅当传入时）     |


---



## 8. 删除记录接口



### 接口描述

根据登录用户与记录 `id` 删除数据库 `api_visitrecord` 表中对应记录。

### 请求信息

- **URL**: `POST /api/file/delete-record/`
- **Method**: `POST`



### 请求参数


| 参数名             | 类型      | 必填  | 默认值 | 说明                      |
| --------------- | ------- | --- | --- | ----------------------- |
| `Authorization` | Header  | 是   | -   | `Bearer <access_token>` |
| `id`            | Integer | 是   | -   | 走访记录ID，需属于当前登录用户        |




### 成功响应

**Status Code**: `200 OK`

```json
{
    "status": "success",
    "message": "删除成功",
    "record_id": 1
}
```



### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "id 不能为空"
}
```

```json
{
    "status": "error",
    "message": "走访记录 ID=1 不存在"
}
```



### 示例请求

```bash
curl -X POST http://localhost:8000/api/file/delete-record/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1"
```

---



## 9. 获取音频文件接口



### 接口描述

根据登录用户与记录 `id` 从数据库 `api_visitrecord` 表中获取对应的音频文件 URL，从 MinIO 存储中读取音频文件并返回给前端，支持直接播放。

### 请求信息

- **URL**: `POST /api/file/get-audio-file/`
- **Method**: `POST`



### 请求参数


| 参数名             | 类型      | 必填  | 默认值 | 说明                      |
| --------------- | ------- | --- | --- | ----------------------- |
| `Authorization` | Header  | 是   | -   | `Bearer <access_token>` |
| `id`            | Integer | 是   | -   | 走访记录ID，需属于当前登录用户        |




### 成功响应

**Status Code**: `200 OK`

成功时直接返回音频文件二进制流，浏览器可直接播放。响应头包含：


| 响应头                   | 说明                                                                           |
| --------------------- | ---------------------------------------------------------------------------- |
| `Content-Type`        | 根据文件扩展名自动识别，支持 `audio/m4a`、`audio/mpeg`、`audio/wav`、`audio/ogg`、`audio/flac` |
| `Content-Disposition` | `inline; filename={文件名}`，表示内联播放                                              |




### 失败响应

**Status Code**: `400 Bad Request`

```json
{
    "status": "error",
    "message": "id 不能为空"
}
```

```json
{
    "status": "error",
    "message": "走访记录 ID=1 不存在"
}
```

```json
{
    "status": "error",
    "message": "该走访记录没有关联的音频文件"
}
```

**Status Code**: `500 Internal Server Error`

```json
{
    "status": "error",
    "message": "从MinIO获取文件失败: S3Error: ..."
}
```



### 示例请求

```bash
curl -X POST http://localhost:8000/api/file/get-audio-file/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1" \
  -o audio.m4a
```



### 前端使用示例

**JavaScript**:

```javascript
// 获取音频文件并播放
async function playAudio(recordId, creatorId) {
    const response = await fetch('/api/file/get-audio-file/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': `Bearer ${token}`
        },
        body: `id=${recordId}`
    });

    if (!response.ok) {
        const error = await response.json();
        console.error('获取音频失败:', error.message);
        return;
    }

    const blob = await response.blob();
    const audioUrl = URL.createObjectURL(blob);
    
    const audio = new Audio(audioUrl);
    audio.play();
    
    audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
    };
}
```

---



## 接口调用流程

```
客户端上传文件 → 创建走访记录 → 调用语音转文字接口 → 建立WebSocket → 接收转写结果 → 调用总结接口
    ↓                    ↓                      ↓                ↓                    ↓
POST /upload/         DB记录               POST /speech-to-text/   ws://localhost:8000/ws/asr/{job_id}/   POST /summarize/
    ↓              (JWT用户)                 (id)                     ↓                    (id)
 上传到MinIO        id, audio_url)              ↓                  等待推送                  ↓
    ↓                                          ↓                    ↓                    查询DB获取original_text
 创建VisitRecord                           查询DB获取audio_url   转写结果                    ↓
 (含MinIO URL)                                  ↓                    ↓                    调用外部总结API
                                              从MinIO下载文件      连接关闭                    ↓
                                                 ↓                                         更新DB: ai_summary
                                              调用外部ASR API
                                              创建任务（返回job_id）
                                              ↓
                                         后台线程轮询状态
                                         (每5秒查询一次，最多10分钟)
                                              ↓
                                         任务完成 → 推送结果 → 删除任务
                                              ↓
                                         更新DB: original_text + status
```

---



## 错误码说明


| HTTP 状态码 | 说明                          |
| -------- | --------------------------- |
| `400`    | 请求参数错误（文件不存在、file_url为空等）   |
| `500`    | 服务器内部错误（MinIO操作失败、API调用失败等） |


---



## 测试指南



### 环境准备

1. **启动 MinIO**:
  ```bash
   minio server ~/minio-data --console-address ":9001"
  ```
   访问 [http://localhost:9001](http://localhost:9001) 登录，创建 bucket "xiaozhu"
2. **启动 Redis**:
  ```bash
   /opt/homebrew/opt/redis/bin/redis-server /opt/homebrew/etc/redis.conf --daemonize yes
  ```
   验证: `/opt/homebrew/opt/redis/bin/redis-cli ping` 应返回 `PONG`
3. **启动后端服务**:
  ```bash
   cd /xiaozhu/xiaozhu_backend
   source .venv/bin/activate
   daphne xiaozhu_backend.asgi:application -b 0.0.0.0 -p 8000
  ```



### 测试步骤



#### 步骤1: 上传音频文件

```bash
curl -X POST http://localhost:8000/api/file/upload/ \
  -F "file=@test.m4a" \
  -F "customer_name=测试用户" \
  -F "visit_time=2026-07-20" \
  -F "status=1"
```

预期响应:

```json
{
    "status": "success",
    "message": "文件上传成功",
    "file_url": "http://localhost:9000/xiaozhu/xxx.m4a",
    "record_id": 1
}
```



#### 步骤2: 提交转写任务

```bash
curl -X POST http://localhost:8000/api/file/speech-to-text/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1"
```

预期响应:

```json
{
    "status": "success",
    "message": "转写任务已提交",
    "job_id": "3b97f597455c4296b98861d8f0225196",
    "record_id": 1
}
```



#### 步骤3: 通过 WebSocket 获取结果

**方法A: 使用 Python**

创建测试脚本 `test_ws.py`:

```python
import asyncio
import websockets
import json

async def main():
    job_id = input("请输入 job_id: ").strip()
    async with websockets.connect(f'ws://localhost:8000/ws/asr/{job_id}/') as ws:
        print(f'已连接到 ws://localhost:8000/ws/asr/{job_id}/')
        print('等待转写结果...')
        message = await ws.recv()
        data = json.loads(message)
        print('\n转写结果:')
        print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
```

运行:

```bash
pip install websockets
python test_ws.py
```

**方法B: 使用 wscat（Node.js）**

```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws/asr/{job_id}/
```

**方法C: 使用浏览器控制台**

打开浏览器开发者工具（F12），在 Console 中执行:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/asr/{job_id}/');
ws.onmessage = e => console.log(JSON.parse(e.data));
ws.onclose = () => console.log('连接关闭');
```



#### 步骤4: 调用总结接口

转写完成后，调用总结接口对录音内容进行 AI 总结：

```bash
curl -X POST http://localhost:8000/api/file/summarize/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1"
```

预期响应:

```json
{
    "status": "success",
    "message": "总结成功",
    "ai_summary": "总结内容...",
    "record_id": 1
}
```



#### 步骤5: 获取记录ID列表

获取指定用户下所有走访记录的 ID 列表：

```bash
curl -X POST http://localhost:8000/api/file/record-ids/ \
  -H "Authorization: Bearer $TOKEN"
```

预期响应:

```json
{
    "status": "success",
    "message": "获取成功",
    "records": [
        [1, "success", "张三", 120, "2026-07-20T10:30:00"],
        [2, "pending", "李四", 60, "2026-07-21T14:15:00"]
    ]
}
```



#### 步骤6: 获取记录详情

根据记录 ID 获取完整的走访记录信息：

```bash
curl -X POST http://localhost:8000/api/file/record-detail/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1"
```

预期响应:

```json
{
    "status": "success",
    "message": "获取成功",
    "data": {
        "id": 1,
        "creator_id": 1,
        "customer_name": "张三",
        "audio_url": "http://localhost:9000/xiaozhu/xxx.m4a",
        "original_text": "[{'start': 0.0, 'end': 2.58, 'text': '你好...', ...}]",
        "ai_summary": "总结内容...",
        "visit_time": "2026-07-20T10:30:00",
        "duration_seconds": 120,
        "business_type": null,
        "status": "success"
    }
}
```



#### 步骤7: 更新录音文本

更新指定记录的录音转写文本内容：

```bash
curl -X POST http://localhost:8000/api/file/update-original-text/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=1" \
  -d "original_text=新的转写文本内容..."
```

预期响应:

```json
{
    "status": "success",
    "message": "更新成功",
    "record_id": 1
}
```



### 注意事项

1. **WebSocket 连接必须在提交转写任务之后建立**，但可以在任务完成之前任意时间建立
2. 如果转写任务在 WebSocket 连接建立之前已经完成，服务端会立即推送已有结果
3. 转写任务最长等待时间为 **10分钟**（120次轮询 × 5秒），超时后服务端会推送错误消息
4. 转写完成后，服务端会主动关闭 WebSocket 连接
5. 如果需要重新转写，需要重新调用 `POST /api/file/speech-to-text/` 获取新的 `job_id`



### 调试技巧

1. **查看后端日志**: daphne 启动后会输出日志，包括 WebSocket 连接和消息推送情况
2. **查看数据库状态**: 可以通过 Django admin（[http://localhost:8000/admin/）查看](http://localhost:8000/admin/）查看) `api_visitrecord` 表的状态变化
3. **测试 WebSocket 连接**: 使用以下命令测试 WebSocket 是否正常工作
  ```bash
   wscat -c ws://localhost:8000/ws/asr/test123/
  ```



### 完整测试示例

```bash
# 1. 上传文件
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/file/upload/ \
  -F "file=@test.m4a" \
  -F "customer_name=测试" \
  -F "visit_time=2026-07-20")
echo "上传结果: $UPLOAD_RESPONSE"

# 2. 提取 record_id
RECORD_ID=$(echo $UPLOAD_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['record_id'])")
echo "record_id: $RECORD_ID"

# 3. 提交转写任务
STT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/file/speech-to-text/ \
  -H "Authorization: Bearer $TOKEN" \
  -d "id=$RECORD_ID")
echo "转写任务提交结果: $STT_RESPONSE"

# 4. 提取 job_id
JOB_ID=$(echo $STT_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
echo "job_id: $JOB_ID"

# 5. 通过WebSocket获取结果
python3 -c "
import asyncio
import websockets
import json

async def get_result():
    async with websockets.connect('ws://localhost:8000/ws/asr/$JOB_ID/') as ws:
        print(f'连接到 ws://localhost:8000/ws/asr/$JOB_ID/')
        print('等待结果...')
        msg = await ws.recv()
        print('\\n转写结果:')
        print(json.dumps(json.loads(msg), ensure_ascii=False, indent=2))

asyncio.run(get_result())
"
```


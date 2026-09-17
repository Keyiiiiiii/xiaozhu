# 榕小助

榕小助是一套面向一线走访场景的移动应用，包含 UniApp 前端和 Django 后端。系统提供用户认证、角色权限、走访记录、音频上传与转写、待办事项、通知分发、知识库文件和应用版本更新等能力。

## 项目结构

```text
xiaozhu/
├── xiaozhu_frontend/            # UniApp 前端（App / H5）
├── xiaozhu_backend/             # Django 后端
│   ├── api/                     # 认证、走访、待办、通知、版本等核心业务
│   ├── file_upload/             # 文件上传及音频处理
│   ├── knowledge/               # 知识库文件管理及外部知识库接口
│   ├── xiaozhu_backend/         # Django 配置、路由、ASGI / WSGI
│   ├── API_DOC.md               # 后端接口文档
│   └── manage.py
├── docs/                        # 产品、设计及联调文档
└── requirements.txt             # Python 依赖
```

主要运行依赖：

- **MySQL**：保存用户、权限、走访、待办、通知、版本和知识库文件元数据。
- **Redis**：作为 Django Channels 的消息通道，支持转写结果的 WebSocket 推送。
- **MinIO**：保存上传的音频等文件。
- **ASR 服务**：提供语音转文字能力。
- **知识库服务**：提供知识文件同步及相关能力。

接口细节见 [`xiaozhu_backend/API_DOC.md`](xiaozhu_backend/API_DOC.md)，前端联调步骤见 [`docs/榕小助_前端联调交接说明.md`](docs/榕小助_前端联调交接说明.md)。

## 环境准备

### 1. 激活 Python 虚拟环境

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 2. 安装依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

### 3. 创建 MySQL 数据库

确保本机已安装并启动 MySQL，然后执行：

```sql
CREATE DATABASE rongxiaozhu
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 4. 配置环境变量

复制后端提供的模板文件，不要直接在 `settings.py` 中填写本地数据库密码：

```bash
cd xiaozhu_backend

# Windows PowerShell
Copy-Item xiaozhu_backend/.env.example .env

# macOS / Linux
cp xiaozhu_backend/.env.example .env
```

按本地环境修改 `xiaozhu_backend/.env`：

```dotenv
DB_NAME=rongxiaozhu
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

`.env` 只用于本地配置，不应提交真实密码或其他密钥。

### 5. 初始化数据库

在 `xiaozhu_backend` 目录执行：

```bash
python manage.py migrate
python manage.py seed_test_users
```

当模型发生变更时，应先生成并审查迁移，再执行迁移：

```bash
python manage.py makemigrations
python manage.py migrate
```

应用版本接口需要测试数据时，可执行：

```bash
python manage.py seed_app_versions
```

> 当前仓库存在尚未补齐的数据库迁移。全新数据库在执行上述命令前，请先阅读[数据库已知问题](#数据库已知问题)。

## 启动后端

仅调试普通 HTTP 接口（例如登录）时：

```bash
cd xiaozhu_backend
python manage.py runserver
```

需要音频转写和 WebSocket 推送时，请先启动 Redis、MinIO 及所需外部服务，再使用 ASGI 服务启动：

```bash
cd xiaozhu_backend
daphne xiaozhu_backend.asgi:application -b 0.0.0.0 -p 8000
```

如需访问 Django Admin，可另行创建管理员账号：

```bash
python manage.py createsuperuser
```

前端的服务地址及真机调试配置见[前端联调交接说明](docs/榕小助_前端联调交接说明.md)。

## 测试账号

执行 `python manage.py seed_test_users` 后会创建以下账号：

| 登录工号 / 用户名 | 密码 | 姓名 | 角色 | 组织 |
| --- | --- | --- | --- | --- |
| `admin` | `123456` | 张三 | 一线人员（`frontline`） | 市公司 / 政企客户部 / 第一网格 |
| `FZ10086` | `123456` | 李四 | 区县专项（`district`） | 市公司 / 鼓楼区 / 第二网格 |
| `FZ10000` | `123456` | 王五 | 市公司（`city`） | 市公司 |

登录接口的 `username` 字段可以填写工号；种子数据中的用户名与工号相同。

角色权限如下：

| 角色 | 接收通知 | 向一线下达通知 | 向区县专项下达通知 |
| --- | --- | --- | --- |
| 一线人员（`frontline`） | 是 | 否 | 否 |
| 区县专项（`district`） | 是 | 是 | 否 |
| 市公司（`city`） | 否 | 是 | 是 |

`seed_test_users` 使用 `update_or_create`，可重复执行。每次执行都会同步角色、权限和上述用户资料，并将三个账号的密码重新设置为 `123456`。

> 这些账号和弱密码仅用于本地开发及联调，禁止用于生产环境或可被公网访问的环境。

## 数据库设计概览

### 权限与用户

- `Permission`：功能级权限点；`code` 唯一。
- `Role`：业务角色；`code` 唯一，通过多对多关系关联 `Permission`，并按 `level` 排序。
- `User`：继承 Django `AbstractUser`；`work_id` 唯一，通过外键关联 `Role`，并保存姓名和组织信息。

角色被用户、通知或额度规则引用时使用 `PROTECT`，避免误删角色导致授权及业务数据失去含义。用户的角色允许为空，便于数据迁移或暂未分配角色的场景。

### 走访与待办

- `VisitRecord`：保存创建人、走访对象、音频 URL、转写 JSON、AI 总结、业务类型、时长及处理状态。
- `TodoItem`：保存负责人、标题、日期、时间、优先级、状态及是否由 AI 生成，可选关联一条走访记录。

删除用户时，其走访记录和负责的待办会通过 `CASCADE` 一并删除；删除走访记录时，关联待办会通过 `SET_NULL` 保留，但不再指向原走访记录。

### 通知与额度

- `Notification`：保存通知标题、内容、发送层级、发送人和读状态。
- `QuotaRule`：为每个角色配置一条月度推送额度，通过一对一关系保证同一角色最多一条规则。

删除通知发送人时通知会通过 `CASCADE` 删除；被通知或额度规则引用的角色受 `PROTECT` 保护。

### 应用版本

- `AppVersion`：保存平台、语义版本号、构建号、更新类型、下载地址、更新日志、静默更新标志、启用状态及创建时间。
- 当前模型按 `version_code` 和创建时间倒序，并为平台与启用状态建立联合索引，以支持查询某平台最新启用版本。
- `update_type`：`0` 提示热更、`1` 强制热更、`2` 提示整包、`3` 强制整包。

### 知识库文件

- `KnowledgeFile`：保存文件名、URL、大小、类型及上传时间；数据库仅保存元数据，实际文件及知识处理由外部存储和知识库服务负责。

### 主要关系

```text
Permission  * <──> *  Role
Role        1 <──  *  User
Role        1 <──  *  Notification
Role        1 <──  0..1 QuotaRule
User        1 <──  *  VisitRecord
User        1 <──  *  TodoItem
User        1 <──  *  Notification
VisitRecord 1 <──  *  TodoItem（可选关联）
```

## 数据库已知问题

当前模型定义与仓库中的迁移文件并未完全同步：

1. **`AppVersion` 迁移缺失**：现有初始迁移仍使用旧字段 `is_forced`，而当前模型已经改为 `version_code`、`update_type`、`is_silent`、`is_active`、`created_at`，并增加了平台/启用状态索引。仓库中尚无迁移完成这些变更。
2. **`KnowledgeFile` 迁移缺失**：`knowledge` 应用存在 `KnowledgeFile` 模型，但其 `migrations` 目录当前没有初始迁移，因此全新数据库执行 `migrate` 不会创建对应数据表。
3. **影响范围**：迁移补齐前，全新环境中的版本检查、`seed_app_versions` 和知识库文件功能可能因字段或数据表不存在而失败。认证、角色和走访等已存在迁移的功能不代表上述功能也已可用。

在修复这些问题时，应生成并审查新的迁移文件，避免直接手工修改生产数据库或改写已在其他环境执行过的历史迁移。

## 测试

认证及鉴权测试：

```bash
cd xiaozhu_backend
python manage.py test api.tests.test_auth
```

版本更新测试依赖正确的 `AppVersion` 表结构；在补齐迁移之前不应将其失败简单归因于接口代码。

更完整的手工验收清单见 [`docs/榕小助_前端联调交接说明.md`](docs/榕小助_前端联调交接说明.md)。

## 常见问题

| 现象 | 排查方式 |
| --- | --- |
| 登录失败 | 检查 MySQL 配置，并确认已执行 `migrate` 和 `seed_test_users`。 |
| 业务接口返回 401 | 确认已登录，访问令牌未过期，且请求头为 `Authorization: Bearer <token>`。 |
| 上传或 MinIO 报错 | 确认 MinIO 已启动、连接配置正确且目标 bucket 已创建。 |
| 转写 WebSocket 无法连接 | 使用 `daphne` 启动后端，并确认 Redis 和 ASR 服务可用。 |
| 真机无法连接后端 | 将前端服务地址改为后端电脑的局域网 IP，并确保手机与电脑处于同一网络。 |
| 版本或知识库接口提示表/字段不存在 | 对照[数据库已知问题](#数据库已知问题)，确认所需迁移是否已经补齐并执行。 |


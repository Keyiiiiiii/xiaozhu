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

项目部署环境已准备 Python 虚拟环境，进入项目根目录后按操作系统激活：

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

进入包含 `manage.py` 的外层 `xiaozhu_backend` 目录执行：

```bash
cd xiaozhu_backend
python manage.py migrate
python manage.py seed_test_users
```

`python manage.py migrate` 会一次性执行所有已注册应用的迁移，包括 `api`、`knowledge` 和 Django 内置应用；不需要进入 `knowledge` 目录再次执行。

开发阶段修改模型后，应在开发环境生成并审查迁移：

```bash
python manage.py makemigrations
python manage.py migrate
```

服务器部署时只执行仓库中已经提交的迁移，不要在服务器上运行 `makemigrations`。

应用版本接口需要测试数据时，可执行：

```bash
python manage.py seed_app_versions
```

执行完成后可检查迁移状态：

```bash
python manage.py showmigrations api knowledge
```

正常情况下，`api` 的 `0001` 至 `0006` 以及 `knowledge` 的 `0001` 均应显示为 `[X]`。全新数据库会同时创建业务表和 `knowledge_knowledgefile`，无需手工创建知识库表。

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
| `admin` | `123456` | 张三 | 一线人员（`frontline`） | 市公司 / 测试区县 / 第一网格 |
| `FZ10086` | `123456` | 李四 | 区县专项（`district`） | 市公司 / 鼓楼区 |
| `FZ10000` | `123456` | 王五 | 市公司（`city`） | 市公司 / 市公司本部 |

登录接口的 `username` 字段可以填写工号；种子数据中的用户名与工号相同。

角色权限如下：

| 角色 | 接收通知 | 向一线下达通知 | 向区县专项下达通知 |
| --- | --- | --- | --- |
| 一线人员（`frontline`） | 是 | 否 | 否 |
| 区县专项（`district`） | 是 | 是 | 否 |
| 市公司（`city`） | 是 | 是 | 是 |

`seed_test_users` 使用 `update_or_create`，可重复执行。每次执行都会同步角色、权限和上述用户资料，并将三个账号的密码重新设置为 `123456`。

> 这些账号和弱密码仅用于本地开发及联调，禁止用于生产环境或可被公网访问的环境。

## 数据库设计概览

### 权限与用户

- `Permission`：功能级权限点；`code` 唯一。
- `Role`：业务角色；`code` 唯一，通过多对多关系关联 `Permission`，并按 `level` 排序。
- `Department`：市公司部门，`code` 唯一；当前仅用于人员归属和发布者展示。
- `District`：区县，`code` 唯一。
- `Grid`：网格，同一区县内 `code` 唯一，并通过外键关联 `District`。
- `User`：继承 Django `AbstractUser`；`work_id` 唯一，通过外键关联 `Role`、`Department`、`District` 和 `Grid`，并保留 `organization` 文本用于兼容展示。

角色和组织外键使用 `PROTECT`，避免删除仍被用户或业务数据引用的角色、部门、区县和网格。区县角色必须关联区县；一线角色必须关联区县和网格，且网格必须属于用户选择的区县。

### 走访与待办

- `VisitRecord`：保存创建人、走访对象、音频 URL、转写 JSON、AI 总结、业务类型、时长及处理状态。
- `TodoItem`：保存负责人、标题、日期、时间、优先级、状态及是否由 AI 生成，可选关联一条走访记录。

删除用户时，其走访记录和负责的待办会通过 `CASCADE` 一并删除；删除走访记录时，关联待办会通过 `SET_NULL` 保留，但不再指向原走访记录。

### 通知与额度

- `Notification`：保存标题、正文、紧急程度、发布范围、目标区县或网格、发布者、强制展示配置、发布时间、过期时间和撤回状态。
- `NotificationReceiver`：保存通知与用户的接收快照，以及每个用户独立的已读时间和强制展示确认时间。
- `QuotaRule`：为每个角色配置一条月度推送额度，通过一对一关系保证同一角色最多一条规则。

通知发布者使用 `PROTECT`，避免删除账号后丢失发布审计；删除通知时通过 `CASCADE` 删除对应接收快照，接收人用户使用 `PROTECT`。通知范围支持市公司、区县和网格，发布时按有效用户、组织外键及 `notify.receive` 权限生成接收人快照。

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
Role        1 <──  0..1 QuotaRule
Department  1 <──  *  User（可选关联）
District    1 <──  *  Grid
District    1 <──  *  User（可选关联）
Grid        1 <──  *  User（可选关联）
User        1 <──  *  VisitRecord
User        1 <──  *  TodoItem
User        1 <──  *  Notification（作为发布者）
Notification 1 <── * NotificationReceiver
User          1 <── * NotificationReceiver
VisitRecord 1 <──  *  TodoItem（可选关联）
```

## 数据库迁移说明

- `api/0004_sync_appversion_schema` 将旧版 `AppVersion` 结构升级为当前字段和索引。
- `api/0005_organization_models` 创建部门、区县和网格表，并为用户增加组织外键。
- `api/0006_notification_delivery_models` 升级通知结构并创建通知接收人表。
- `knowledge/0001_initial` 创建 `knowledge_knowledgefile`；如果旧环境已手工创建同名表，迁移会保留现有表并登记迁移状态。

全新部署应创建空数据库后直接运行 `python manage.py migrate`，不要先手工创建业务表，也不要导入包含旧版业务表结构的全量 SQL。需要恢复知识库记录时，应先由迁移创建最新表结构，再仅导入与当前 `KnowledgeFile` 字段匹配的数据。

## 测试

认证及鉴权测试：

```bash
cd xiaozhu_backend
python manage.py test api.tests.test_auth
```

版本更新测试依赖已执行到 `api/0004` 及以上的 `AppVersion` 表结构。

更完整的手工验收清单见 [`docs/榕小助_前端联调交接说明.md`](docs/榕小助_前端联调交接说明.md)。

## 常见问题

| 现象 | 排查方式 |
| --- | --- |
| 登录失败 | 检查 MySQL 配置，并确认已执行 `migrate` 和 `seed_test_users`。 |
| 业务接口返回 401 | 确认已登录，访问令牌未过期，且请求头为 `Authorization: Bearer <token>`。 |
| 上传或 MinIO 报错 | 确认 MinIO 已启动、连接配置正确且目标 bucket 已创建。 |
| 转写 WebSocket 无法连接 | 使用 `daphne` 启动后端，并确认 Redis 和 ASR 服务可用。 |
| 真机无法连接后端 | 将前端服务地址改为后端电脑的局域网 IP，并确保手机与电脑处于同一网络。 |
| 版本或知识库接口提示表/字段不存在 | 执行 `python manage.py showmigrations api knowledge`，确认 `api/0001` 至 `0006` 和 `knowledge/0001` 均已执行。 |


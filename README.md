# 数据库初始化

**前端联调**：请先阅读 [`docs/榕小助_前端联调交接说明.md`](docs/榕小助_前端联调交接说明.md)（测试账号、config 改 IP、验收清单）。

### 1. 激活虚拟环境

```bash
# Windows 系统:
.\venv\Scripts\activate

# Mac/Linux 系统:
source venv/bin/activate
```

### 2. 安装依赖并生成数据库

```bash
# 确保已安装 MySQL
pip install -r requirements.txt
```

### 3. 本地手动建库

```bash
# 打开MySQL命令行执行以下语句
CREATE DATABASE rongxiaozhu
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 4. 配置本地环境变量

修改/xiaozhu_backend/xiaozhu_backend/settings.py文件line92，改为你自己的mysql密码

在 xiaozhu_backend下，找到提供的模板文件 .env.example，将该文件复制一份，并重命名为 .env，将其中的参数修改为你个人的本地 MySQL 配置：

```bash
DB_NAME=rongxiaozhu
DB_USER=root
DB_PASSWORD=你本地MySQL的真实密码
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 5.同步数据表结构(models有变更时)

```bash
cd xiaozhu_backend
python manage.py makemigrations api
python manage.py migrate
python manage.py seed_test_users
```

`seed_test_users` 会写入可登录测试账号（`admin / 123456`），零数据环境联调前必须执行，可重复运行。

### 6.启动开发服务器

```bash
python manage.py runserver
```

语音转文字后端用下面命令启动：

```bash
daphne xiaozhu_backend.asgi:application -b 0.0.0.0 -p 8000
```

### 7.创建管理员账号

```bash
# 如果需要登录 Django Admin 网页后台查看数据
python manage.py createsuperuser
```


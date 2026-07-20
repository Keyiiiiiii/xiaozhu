# 数据库初始化

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

在 xiaozhu_backend下，找到提供的模板文件 .env.example，将该文件复制一份，并重命名为 .env，将其中的参数修改为你个人的本地 MySQL 配置：

```bash
DB_NAME=rongxiaozhu
DB_USER=root
DB_PASSWORD=你本地MySQL的真实密码
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 5.同步数据表结构

```bash
python manage.py migrate
```

### 6.启动开发服务器

```bash
python manage.py runserver
```

### 7.创建管理员账号

```bash
# 如果需要登录 Django Admin 网页后台查看数据
python manage.py createsuperuser
```
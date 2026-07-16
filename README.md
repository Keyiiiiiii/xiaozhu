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
pip install -r requirements.txt
cd xiaozhu_backend
python manage.py migrate
```
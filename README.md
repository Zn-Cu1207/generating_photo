
```
fastapi-project/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口文件
│   ├── config.py           # 配置文件
│   ├── database.py         # 数据库连接
│   ├── models/             # 数据模型。     业务数据存储相关定义。    一般关联数据库
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   ├── schemas/            # Pydantic 模型.       外部输入输出定义
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   ├── api/               # API 路由
│   │   ├── __init__.py
│   │   ├── v1/            # API 版本
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── users.py
│   │   │   │   ├── items.py
│   │   │   │   └── auth.py
│   │   │   └── api.py    # API 路由注册
│   │   └── dependencies.py # 依赖项
│   ├── core/              # 核心功能
│   │   ├── __init__.py
│   │   ├── security.py    # 安全相关
│   │   └── exceptions.py  # 自定义异常
│   ├── crud/              # CRUD 操作
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── item.py
│   └── utils/             # 工具函数
│       ├── __init__.py
│       └── validators.py
├── tests/                 # 测试文件
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_users.py
│   └── test_items.py
├── alembic/              # 数据库迁移
│   ├── versions/
│   └── alembic.ini
├── .env                  # 环境变量
├── .env.example          # 环境变量示例
├── requirements.txt      # 依赖包
├── requirements-dev.txt  # 开发依赖
├── Dockerfile           # Docker 配置
├── docker-compose.yml   # Docker Compose
└── README.md            # 项目说明

```
# 小车自动配送系统后端

## 项目简介
小车自动配送系统的后端服务，提供配送任务管理、路径规划、车辆调度等核心功能。

## 项目结构
```
last-mile-backend/
├── app/                    # 应用主目录
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑服务
│   ├── utils/             # 工具函数
│   └── db/                # 数据库相关
│   └── schemas/           # 数据验证模型
├── tests/                 # 测试文件
├── docs/                  # 文档
├── scripts/               # 脚本文件
├── requirements.txt       # 依赖包
├── .gitignore            # Git忽略文件
└── docker-compose.yml    # Docker配置
```

## 技术栈
- FastAPI: Web框架
- SQLAlchemy: ORM
- PostgreSQL: 数据库
- Redis: 缓存
- Celery: 异步任务队列
- Docker: 容器化部署

## 快速开始
1. 安装依赖: `pip install -r requirements.txt`
2. 配置环境变量
3. 启动服务: `uvicorn app.main:app --reload`
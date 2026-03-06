# Last-Mile Delivery Backend

这是一个基于 FastAPI 构建的无人车末端配送后端服务。它为无人配送车队、配送任务、用户交互和后台管理提供了一套完整的 API 解决方案。

## ✨ 核心功能

- **用户管理与认证**: 支持用户注册、登录，并使用 JWT (JSON Web Tokens) 进行身份验证。
- **车辆管理**: 管理无人车基本信息、状态更新和实时位置追踪。
- **任务调度**: 创建、分配和更新配送任务。
- **预约系统**: 用户可以预约上门取件服务。
- **快递追踪**: 管理和追踪快递包裹的状态。
- **地理编码**: 集成腾讯地图 API，提供地址到坐标的转换服务。
- **数据库迁移**: 使用 Alembic 管理数据库结构变更，确保开发与生产环境的一致性。

## 🛠️ 技术栈

- **后端框架**: [FastAPI](https://fastapi.tiangolo.com/)
- **数据库 ORM**: [SQLAlchemy](https://www.sqlalchemy.org/)
- **数据库迁移**: [Alembic](https://alembic.sqlalchemy.org/)
- **数据校验**: [Pydantic](https://docs.pydantic.dev/)
- **数据库**: [PostgreSQL](https://www.postgresql.org/)
- **Web 服务器**: [Uvicorn](https://www.uvicorn.org/)

## 🚀 环境准备与安装

在开始之前，请确保你已经安装了 Python 3.11+ 和 PostgreSQL。

1.  **克隆仓库**
    ```bash
    git clone <your-repository-url>
    cd last-mile-backend
    ```

2.  **创建并激活虚拟环境**
    ```bash
    # Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # macOS / Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置环境变量**
    -   复制 `.env.example` 文件并重命名为 `.env`。
    -   根据你的本地环境修改 `.env` 文件中的配置，特别是 `DATABASE_URL` 和 `SECRET_KEY`。
    ```ini
    # .env
    DATABASE_URL="postgresql://user:password@host:port/dbname"
    SECRET_KEY="<a-very-secure-random-string>"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    # 腾讯地图 WebService API Key
    TENCENT_MAP_API_KEY="<your-tencent-map-key>"
    TENCENT_MAP_API_SK="<your-tencent-map-sk>"
    ```

5.  **执行数据库迁移**
    使用 Alembic 创建所有数据表。
    ```bash
    python -m alembic upgrade head
    ```

6.  **（可选）初始化管理员账号**
    运行脚本创建一个默认的管理员用户。
    ```bash
    python -m scripts.add_admin
    ```
    默认账号：`admin`，密码：`admin2026` (密码在 `scripts/add_admin.py` 中定义)。

## 🏃‍♂️ 运行项目

```bash
uvicorn app.main:app --reload
```
服务启动后，你可以在 `http://127.0.0.1:8000` 访问。

## 📚 API 文档

项目启动后，FastAPI 会自动生成交互式 API 文档：

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🗄️ 数据库迁移

当 `app/models` 中的模型发生变更时，使用以下命令来生成和应用数据库迁移：

1.  **自动生成迁移脚本**
    ```bash
    python -m alembic revision --autogenerate -m "Your migration message"
    ```

2.  **应用迁移**
    ```bash
    python -m alembic upgrade head
    ```

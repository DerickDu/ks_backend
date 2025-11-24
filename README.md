# 实体管理后端服务

这是一个基于Flask框架开发的后端服务，用于管理和查询实体数据。该服务提供了与PostgreSQL数据库交互的API端点，支持实体数量统计和按域分组统计功能。

## 项目结构

```
ks_backend/
├── app.py                # Flask应用主入口
├── config.py             # 应用配置管理
├── requirements.txt      # 项目依赖
├── .env                  # 环境变量配置
├── start.sh              # 启动脚本
├── check_pep8.py         # PEP 8检查脚本
├── models/               # 数据库模型
│   ├── __init__.py
│   └── models.py
├── routes/               # API路由
│   ├── __init__.py
│   └── entities_routes.py
└── utils/                # 工具函数
    ├── __init__.py
    ├── error_handlers.py
    └── validators.py
```

## 快速开始

### 1. 环境要求

- Python 3.8+
- PostgreSQL 12+

### 2. 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

### 3. 配置环境变量

复制`.env`文件并根据实际情况修改配置：

```bash
# 数据库连接配置
DATABASE_URL="postgresql://admin:password@localhost:5432/example_db"

# Flask应用配置
FLASK_APP="app.py"
FLASK_ENV="development"
SECRET_KEY="your-secret-key-here"

# 应用配置
APP_NAME="Entity Management API"
APP_VERSION="1.0.0"
```

### 4. 启动服务

使用启动脚本运行服务：

```bash
chmod +x start.sh
./start.sh
```

或者直接运行：

```bash
python3 app.py
```

服务将在`http://0.0.0.0:5000`启动。

## API 文档

### 1. 获取实体总数量

**端点：** `GET /api/entities/count`

**功能：** 查询Entities表中的总记录数。

**响应格式：**
```json
{"total_entities": 123}
```

**状态码：**
- 200: 成功
- 500: 服务器内部错误

### 2. 按域统计实体数量

**端点：** `GET /api/entities/count-by-domain`

**功能：** 按Domain分组统计Entities表中的实体数量。

**响应格式：**
```json
{
    "通信": 15,
    "计算机": 23,
    "人工智能": 42
}
```

**状态码：**
- 200: 成功
- 500: 服务器内部错误

### 3. 获取Domain和SubDomain树形结构

**端点：** `GET /api/entities/domains-tree`

**功能：** 获取所有不同的domain和sub_domain数据，并转换为Ant Design Tree组件所需的数据格式。

**查询参数：**
- `refresh` (可选，布尔值): 强制刷新缓存，立即重新计算树形结构

**响应格式：**
```json
[
    {
        "key": "domain1",
        "title": "领域名称1",
        "children": [
            {
                "key": "domain1_subdomain1",
                "title": "子领域1"
            },
            {
                "key": "domain1_subdomain2",
                "title": "子领域2"
            }
        ]
    },
    {
        "key": "domain2",
        "title": "领域名称2"
    }
]
```

**状态码：**
- 200: 成功
- 500: 服务器内部错误

### 4. 获取实体和目录树形结构

**端点：** `GET /api/entities-tree`

**功能：** 根据指定的domain和sub_domain获取对应的实体和目录树形结构，返回符合Ant Design Tree格式的数据。

**查询参数：**
- `domain` (必需，字符串): 指定要查询的域
- `sub_domain` (必需，字符串): 指定要查询的子域
- `refresh` (可选，布尔值): 设置为 `true` 时强制刷新缓存

**响应格式：**
```json
[
  {
    "key": "通信/无线通信/5G",
    "title": "5G",
    "isLeaf": false,
    "children": [
      {
        "key": "通信/无线通信/5G/毫米波",
        "title": "毫米波",
        "isLeaf": true,
        "entity_id": 10,
        "children": []
      },
      {
        "key": "通信/无线通信/5G/大规模MIMO",
        "title": "大规模MIMO",
        "isLeaf": true,
        "entity_id": 11,
        "children": []
      }
    ],
    "entity_id": 8
  },
  {
    "key": "通信/无线通信/WiFi",
    "title": "WiFi",
    "isLeaf": true,
    "entity_id": 9,
    "children": []
  }
]
```

**状态码：**
- 200: 成功获取实体树结构
- 400: 请求参数错误
- 500: 服务器内部错误

### 5. 健康检查

**端点：** `GET /health`

**功能：** 检查服务和数据库连接状态。

**响应格式：**
```json
{
    "status": "healthy",
    "app_name": "Entity Management API",
    "db_status": "connected"
}
```

## 数据库模型

### Entities表
- `entity_id` (BIGINT, 主键)
- `entity_name` (VARCHAR(50), 唯一, 非空)
- `description` (TEXT)
- `validity_result` (BOOLEAN)
- `validity_method` (VARCHAR(255))
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Catalog表
- `entity_id` (关联字段)
- `Path` (VARCHAR(255), 挂接目录路径)
- `Domain` (VARCHAR(100), 最大的父节点)
- `sub_domain` (VARCHAR(100), 第二级节点)

### Entities Source Map表
- 联合主键：`source_id` (BIGINT, 非空)
- 联合主键：`entity_id` (BIGINT, 非空)

### Entities Sources表
- `source_id` (BIGINT, 主键)
- `source_type` (VARCHAR(100), 非空)
- `source_ref` (VARCHAR(255))
- `created_at` (TIMESTAMP)

## 代码风格检查

运行以下命令检查代码是否符合PEP 8规范：

```bash
python3 check_pep8.py
```

## 错误处理

系统实现了完善的错误处理机制，包括：
- 数据库连接错误
- SQL查询错误
- 参数验证错误
- HTTP请求错误

所有API错误响应都遵循统一的格式，包含错误类型和详细描述。

## 性能优化

- 在Catalog表的domain字段上创建了索引，优化按域统计查询
- 使用SQLAlchemy的高效查询模式，避免不必要的数据加载
- 禁用SQLAlchemy的修改跟踪功能，提高性能
- 实现了参数验证，防止恶意请求导致的性能问题

## 安全考虑

- 使用环境变量管理敏感配置信息
- 实现了输入参数验证，防止注入攻击
- 避免在生产环境中暴露详细的错误信息
- 所有数据库查询使用ORM，避免SQL注入风险

## 部署说明

在生产环境中部署时，建议：
1. 设置`FLASK_ENV=production`
2. 使用WSGI服务器（如Gunicorn、uWSGI）运行应用
3. 配置反向代理（如Nginx）
4. 启用HTTPS
5. 定期更新依赖包，修复潜在的安全漏洞
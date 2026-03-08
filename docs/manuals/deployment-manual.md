# OpenYoung 部署手册

> **版本**: 1.0.0
> **更新日期**: 2026-03-02

---

## 1. 系统要求

### 1.1 基础环境

| 项目 | 要求 | 说明 |
|------|------|------|
| **Python** | >= 3.10 | 推荐 3.12+ |
| **操作系统** | Linux/macOS/Windows | - |
| **内存** | >= 4GB | 8GB+ 推荐 |
| **磁盘** | >= 10GB | SSD 推荐 |

### 1.2 依赖服务

| 服务 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.10+ | 运行时 |
| **pip** | Latest | 包管理 |
| **可选: Docker** | Latest | 容器化部署 |
| **可选: Redis** | 6.0+ | 缓存层 |

### 1.3 Python 环境准备

```bash
# 推荐使用 venv 或 conda 创建隔离环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 升级 pip
pip install --upgrade pip
```

---

## 2. 安装部署

### 2.1 本地开发安装

```bash
# 克隆项目
git clone https://github.com/your-org/openyoung.git
cd openyoung

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "from src.agents.young_agent import YoungAgent; print('OK')"
```

### 2.2 使用 Docker 部署

#### 2.2.1 构建镜像

```bash
# 构建镜像
docker build -t openyoung:latest .

# 或使用 docker-compose
docker-compose build
```

#### 2.2.2 Docker Compose 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  openyoung:
    build: .
    ports:
      - "8000:8000"
    environment:
      - YOUNG_ENV=production
      - YOUNG_LOG_LEVEL=info
    volumes:
      - ./config:/app/config
    restart: unless-stopped

  # 可选: Redis 缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f openyoung

# 停止服务
docker-compose down
```

### 2.3 生产环境部署

#### 2.3.1 使用 Gunicorn

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:8000 "src.main:app" --timeout 120

# 使用 systemd 管理
sudo cp deploy/openyoung.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable openyoung
sudo systemctl start openyoung
```

#### 2.3.2 使用 Supervisor

```ini
# /etc/supervisor/conf.d/openyoung.conf
[program:openyoung]
command=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 src.main:app
directory=/path/to/openyoung
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/openyoung.err.log
stdout_logfile=/var/log/openyoung.out.log
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start openyoung
```

---

## 3. 服务配置

### 3.1 环境变量

| 变量名 | 默认值 | 说明 |
|--------|---------|------|
| `YOUNG_ENV` | `development` | 运行环境 |
| `YOUNG_LOG_LEVEL` | `info` | 日志级别 |
| `YOUNG_HOST` | `0.0.0.0` | 监听地址 |
| `YOUNG_PORT` | `8000` | 监听端口 |
| `YOUNG_CONFIG_PATH` | `./config` | 配置目录 |
| `YOUNG_DB_URL` | - | 数据库连接 |
| `YOUNG_REDIS_URL` | - | Redis 连接 |
| `YOUNG_SECRET_KEY` | - | 密钥 |

### 3.2 配置文件

```bash
# 创建配置目录
mkdir -p config

# 复制示例配置
cp config.example.yaml config/production.yaml
```

### 3.3 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# API 文档
curl http://localhost:8000/docs
```

---

## 4. 运维管理

### 4.1 日志管理

```bash
# 查看实时日志
tail -f logs/openyoung.log

# 日志轮转配置 (logrotate)
/var/log/openyoung/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
}
```

### 4.2 监控配置

#### 4.2.1 Prometheus 指标

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('young_requests_total', 'Total requests')
request_duration = Histogram('young_request_duration_seconds', 'Request duration')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

#### 4.2.2 健康检查端点

```python
@app.route('/health')
def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": get_uptime()
    }
```

### 4.3 备份与恢复

```bash
# 备份配置
tar -czf backup/config-$(date +%Y%m%d).tar.gz config/

# 备份数据 (如使用数据库)
pg_dump -U young $YOUNG_DB_NAME > backup/db-$(date +%Y%m%d).sql

# 恢复
tar -xzf backup/config-20260302.tar.gz -C /
```

---

## 5. 性能优化

### 5.1 Python 优化

```bash
# 安装性能优化库
pip install uvloop gunicorn[gevent]

# 使用 uvloop
pip install uvloop

# 配置 gunicorn 使用 gevent
gunicorn -k gevent -w 4 ...
```

### 5.2 缓存策略

```python
# src/cache/redis_cache.py
import redis
from functools import wraps

redis_client = redis.from_url(os.environ.get('YOUNG_REDIS_URL'))

def cache_result(expire=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.setex(key, expire, json.dumps(result))
            return result
        return wrapper
    return decorator
```

---

## 6. 安全配置

### 6.1 防火墙配置

```bash
# Ubuntu (UFW)
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp   # SSH
sudo ufw enable

# 限制 IP 访问
sudo ufw allow from 10.0.0.0/24 to any port 8000
```

### 6.2 SSL/TLS 配置

```bash
# 使用 Certbot 获取证书
sudo certbot --nginx -d api.example.com

# 或使用 Let's Encrypt
sudo certbot certonly --standalone -d api.example.com
```

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 7. 故障排查

### 7.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 启动失败 | 端口占用 | 检查并释放端口 `lsof -i :8000` |
| 导入错误 | 依赖缺失 | `pip install -r requirements.txt` |
| 内存溢出 | 数据过大 | 增加 worker 内存限制 |
| 响应慢 | 阻塞操作 | 使用异步处理 |

### 7.2 调试模式

```bash
# 开启调试模式
export YOUNG_DEBUG=true
export YOUNG_LOG_LEVEL=debug

# 使用 Flask 调试
FLASK_DEBUG=1 python -m flask run
```

### 7.3 日志分析

```bash
# 查看错误日志
grep ERROR logs/openyoung.log

# 查看慢请求
grep "slow" logs/openyoung.log

# 实时监控
tail -f logs/openyoung.log | grep ERROR
```

---

## 8. 升级指南

### 8.1 版本升级

```bash
# 拉取新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt

# 运行迁移
python -m alembic upgrade head

# 重启服务
sudo systemctl restart openyoung
```

### 8.2 回滚操作

```bash
# 查看可用版本
git tag

# 回滚到上一个版本
git revert HEAD
git push origin main

# 或使用 Docker
docker-compose down
docker-compose up --build -d
```

---

## 9. 附录

### 9.1 快速启动命令

```bash
# 一键启动 (开发环境)
make dev

# 一键启动 (生产环境)
make prod

# 运行测试
make test

# 构建 Docker
make docker-build
```

### 9.2 目录结构

```
openyoung/
├── src/                    # 源代码
│   ├── agents/             # Agent 核心
│   ├── flow/              # 流程控制
│   ├── memory/             # 记忆系统
│   ├── prompts/           # 提示词
│   └── ...
├── config/                # 配置文件
├── tests/                 # 测试用例
├── docs/                  # 文档
├── scripts/               # 脚本
├── logs/                  # 日志
├── deploy/                 # 部署配置
└── requirements.txt       # 依赖
```

### 9.3 联系支持

- **文档**: https://docs.openyoung.example.com
- **Issue**: https://github.com/your-org/openyoung/issues
- **Email**: support@openyoung.example.com


---

## 10. 测试部署

### 10.1 E2E 测试

OpenYoung 包含完整的 E2E 测试套件，用于验证核心功能：

```bash
# 运行所有 E2E 测试
pytest tests/e2e/ -v

# 运行 CLI 测试
pytest tests/e2e/test_cli_e2e.py -v

# 运行高级功能测试
pytest tests/e2e/test_advanced_features.py -v

# 运行特定测试
pytest tests/e2e/test_cli_e2e.py::test_llm_api_deepseek -v
```

### 10.2 测试环境变量

E2E 测试需要配置 LLM API Keys：

```bash
# .env 文件示例
DEEPSEEK_API_KEY="sk-xxxx"
MOONSHOT_API_KEY="xxxx"
DASHSCOPE_API_KEY="xxxx"
ZHIPU_API_KEY="xxxx"
```

### 10.3 测试覆盖

E2E 测试覆盖：

- **CLI 命令**: llm, agent, config, package, source
- **LLM API**: DeepSeek, Moonshot, Qwen, GLM
- **Evolver**: Gene, Capsule, EvolutionEvent, Personality
- **FlowSkills**: Sequential, Parallel, Conditional, Loop
- **Harness**: start, pause, resume, stop, stats

### 10.4 验证检查

部署后运行以下验证：

```bash
# 1. 验证 Agent 配置
python -c "from src.cli.main import AgentLoader; print(AgentLoader().list_agents())"

# 2. 验证 LLM Provider
openyoung llm list

# 3. 验证模块导入
python -c "from src.package_manager import PackageManager; from src.evolver import EvolutionEngine; from src.evaluation import EvaluationHub; print('OK')"

# 4. 运行 E2E 测试
pytest tests/e2e/ -v --tb=short
```

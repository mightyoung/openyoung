# OpenYoung Dockerfile
# 一体化部署 - 支持多平台消息接入

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -e .

# 安装可选依赖 (消息平台)
RUN pip install --no-cache-dir \
    python-telegram-bot \
    discord.py \
    aiocp \
    aiohttp

# 创建非 root 用户
RUN useradd -m -u 1000 openyoung && \
    chown -R openyoung:openyoung /app
USER openyoung

# 环境变量
ENV PYTHONPATH=/app
ENV OPENYOUNG_STORAGE=/app/.openyoung

# 暴露端口
EXPOSE 8080 8081 8082 8083

# 入口点
CMD ["python", "-m", "src.cli.main", "run"]

# 标签
LABEL maintainer="OpenYoung Team"
LABEL description="AI Agent with multi-platform messaging support"

# RL 训练 Dockerfile
# 用于独立 RL 训练服务

FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

LABEL maintainer="OpenYoung Team"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements-rl.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements-rl.txt

# 复制代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV RL_ENABLED=true

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "src.agents.rl.trainer", "--port", "8000"]

#!/bin/bash
# OpenYoung WebUI Startup Script

# 默认配置
PORT=${PORT:-8501}
API_URL=${API_URL:-http://localhost:8080}

echo "Starting OpenYoung WebUI on port $PORT"
echo "API URL: $API_URL"

# 启动 Streamlit
cd /app
streamlit run src/webui/app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.enableCors true \
    --theme.base "light" \
    --theme.primaryColor "#0078D4"

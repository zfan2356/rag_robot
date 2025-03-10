# 使用官方 Python 3.12.8 镜像（基于 Debian Bookworm）
FROM python:3.12.8-slim-bookworm AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖（根据实际需要增减）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY src/requirements.txt .

# 安装 Python 依赖（使用清华镜像源加速）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# ---------------------------
# 生产阶段（使用更小的基础镜像）
FROM python:3.12.8-slim-bookworm

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 创建工作目录
WORKDIR /app

# 从 builder 阶段复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY ./src /app/src

# 暴露端口
EXPOSE 8000

# 启动命令（根据实际需要选择）
# 基础启动方式：
CMD ["uvicorn", "src.bot_app.app:app", "--host", "0.0.0.0", "--port", "8000"]

# 生产推荐启动方式（需要安装 gunicorn）：
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]

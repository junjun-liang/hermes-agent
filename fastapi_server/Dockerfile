# Hermes-Agent FastAPI 服务 Docker 镜像

FROM python:3.12-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 创建非 root 用户
RUN groupadd --gid 1000 hermes && \
    useradd --uid 1000 --gid 1000 --create-home hermes

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY fastapi_server/requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY --chown=hermes:hermes fastapi_server/ ./fastapi_server/
COPY --chown=hermes:hermes run_agent.py model_tools.py toolsets.py hermes_state.py hermes_constants.py ./
COPY --chown=hermes:hermes agent/ ./agent/
COPY --chown=hermes:hermes tools/ ./tools/

# 切换到非 root 用户
USER hermes

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/api/v1/health'); exit(0 if r.status_code == 200 else 1)" || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "fastapi_server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

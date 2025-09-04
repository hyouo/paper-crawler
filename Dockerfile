# 使用官方 Python 运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装 gosu 用于以非 root 用户身份运行 (可选，但更安全)
RUN apt-get update && apt-get install -y gosu && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装依赖
# 这样可以利用 Docker 的层缓存机制，只有在 requirements.txt 变动时才重新安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码到容器中
COPY . .

# 创建一个非 root 用户来运行应用
RUN useradd --create-home appuser

# 定义数据卷，用于持久化存储论文和数据库
# 建议在 docker run 命令中使用 -v 参数来挂载主机目录
VOLUME /app/paper
VOLUME /app/paper_crawler.db

# 暴露端口
EXPOSE 8080

# 设置启动命令
# 使用 gosu 以 appuser 用户身份运行，避免权限问题
# CMD ["python", "app.py"]
CMD ["gosu", "appuser", "python", "app.py"]

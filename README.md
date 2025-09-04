# 论文抓取与管理平台

这是一个经过重构和功能增强的科研论文抓取工具。它提供了一个现代化的 Web UI，允许用户方便地配置抓取参数、实时监控抓取过程，并直接浏览、打开和管理下载的论文。

![Web UI Screenshot](ui.png)

## ✨ 主要特性

- **现代化 Web UI**: 使用 Bootstrap 5 构建的响应式、单页应用界面。
- **实时进度更新**: 通过 WebSocket (Socket.IO) 实时显示抓取状态、日志和进度条。
- **在线配置**: 直接在网页上修改关键词、分类等参数并一键保存。
- **持久化存储**: 使用 SQLite 数据库记录所有下载的论文，避免重复下载，方便管理。
- **论文删除功能**: 支持单篇和批量删除已下载论文，同时删除本地存储的 PDF 文件。
- **优化分类筛选**: 右侧论文列表的分类筛选器现在只显示已下载论文中存在的类别，并支持动态更新。
- **修复 arXiv PDF 下载**: 解决了 arXiv 论文 PDF 无法下载的问题。
- **后台任务**: 抓取任务在后台运行，不会阻塞 UI。
- **容器化支持**: 提供 `Dockerfile`，可一键打包部署。
- **保留 CLI**: 依然支持通过命令行运行，方便集成到自动化脚本中。

## 🚀 快速开始 (Web UI 推荐)

这是运行此项目的推荐方式。

### 1. 环境准备

- [Python 3.8+](https://www.python.org/)
- (可选) [Docker](https://www.docker.com/)

### 2. 安装依赖

克隆项目后，在项目根目录运行：

```bash
pip install -r requirements.txt
```

### 3. 启动服务器

```bash
python app.py
```

服务器启动后，你将看到类似以下的输出：

```
INFO:root:启动服务器，访问 http://127.0.0.1:8080
```

现在，打开你的浏览器并访问 [http://127.0.0.1:8080](http://172.0.0.1:8080) 即可开始使用。

### 4. 使用 Docker 运行 (可选)

如果你安装了 Docker，可以更方便地运行本项目。

1.  **构建 Docker 镜像:**
    ```bash
    docker build -t paper-crawler .
    ```

2.  **运行容器:**
    ```bash
    docker run -p 8080:8080 -v "$(pwd)/paper:/app/paper" -v "$(pwd)/paper_crawler.db:/app/paper_crawler.db" paper-crawler
    ```
    - `-p 8080:8080`: 将容器的 8080 端口映射到主机的 8080 端口。
    - `-v "..."`: 将容器内的 `paper` 文件夹（下载目录）和数据库文件挂载到主机当前目录，以实现数据持久化。

## ⚙️ 命令行使用 (CLI)

对于自动化脚本或简单的抓取任务，你依然可以使用命令行。

```bash
# 使用分类模式 (会读取 config.yaml 中的设置)
python -m src.main --mode category

# 使用关键词模式
python -m src.main --mode keyword
```

## 📝 配置说明 (`config.yaml`)

你可以在 Web UI 中直接修改大部分常用配置。也可以手动编辑项目根目录下的 `config.yaml` 文件。

- `fetch_settings`: 抓取相关参数（模式、时间范围、每类最大论文数等）。
- `keywords`: 关键词列表。
- `categories`: arXiv 与 bioRxiv 分类列表。

## 📁 项目结构

```
.
├── app.py              # Web 服务器入口 (Flask + SocketIO)
├── config.yaml         # 配置文件
├── requirements.txt    # Python 依赖
├── Dockerfile          # Docker 配置文件
├── ui.png              # Web UI 截图
├── paper/              # 论文下载目录 (默认 .gitignore)
├── paper_crawler.db    # SQLite 数据库文件
├── templates/          # HTML 模板文件
│   └── index.html
└── src/
  ├── __init__.py
  ├── main.py           # 命令行 (CLI) 入口
  ├── config.py         # 配置加载/保存模块
  ├── utils.py          # 辅助函数 (网络请求, 日志等)
  ├── database.py       # 数据库交互模块
  ├── crawler.py        # 核心抓取服务
  └── fetchers.py       # 各来源 (arXiv, bioRxiv) 的数据获取实现
```

## 📄 许可证

本项目采用 MIT 许可证。详情请见 `LICENSE` 文件。

# 论文抓取与管理平台

这是一个经过重构和功能增强的科研论文抓取工具。

![Web UI Screenshot](ui.png)

## ✨ 主要特性

- **Web UI**:
- **先预览后下载**: 新的工作流首先获取论文元数据列表，用户可以在阅读摘要后，再决定下载哪些论文的 PDF。
- **搜索功能**:
    - 支持按 **关键词**、**分类**、**作者** 甚至 **arXiv ID 列表**进行精确查找。
    - 可自定义 arXiv 结果的 **排序方式** (按提交日期、相关性等)。
- **命令行界面 (CLI)**: 保留了完整的 CLI 功能，包括交互模式和直接执行模式，适合自动化脚本。

## 🚀 快速开始

### 1. 环境准备
- [Python 3.8+](https://www.python.org/)
- (可选) [Docker](https://www.docker.com/)

### 2. 安装依赖
克隆项目后，在项目根目录运行：
```bash
pip install -r requirements.txt
```
### 3. 选择运行方式

#### 方式 A: Web UI (推荐)
这是运行此项目的最常用方式。
```bash
python app.py
```
服务器启动后，打开你的浏览器并访问 [http://127.0.0.1:8080](http://127.0.0.1:8080)。

**新版 UI 使用流程**:
1. 在左侧设置面板中，选择“按分类”或“按关键词”模式。
2. 展开“高级设置”配置作者、排序方式等参数。
3. 点击“开始抓取”按钮。
4. 抓取完成后，论文列表会显示在中间面板。
5. 点击任意一篇论文，其详细信息（包括摘要）将显示在右侧面板。
6. 你可以勾选多篇论文进行“批量下载”，或在右侧详情面板中“下载此论文”。
7. 下载完成后，“打开文件”和“打开文件夹”按钮将变为可用。

#### 方式 B: 命令行界面 (CLI)
对于自动化脚本或喜欢终端的用户，CLI 提供了强大的功能。
```bash
# 启动交互式会话
python -m src.main

# 直接按关键词抓取和下载
python -m src.main --mode keyword
```

---

## 🌍 语言切换

本项目支持中文和英文两种语言。

- **Web UI**: 点击页面右上角的 `语言 (Language)` 下拉菜单即可实时切换。
- **命令行**:
    - 使用 `--lang` 参数启动，例如 `python -m src.main --lang zh`。
    - 在交互模式下，如果没有通过参数指定语言，程序会首先提示您选择语言。

---

## ⚙️ 配置说明 (`config.yaml`)

你可以在 Web UI 中直接修改大部分常用配置，这些设置会自动保存到 `config.yaml`。

### `fetch_settings`
控制抓取行为的核心参数。

| 键 | 类型 | 描述 |
| :--- | :--- | :--- |
| `method` | string | 默认抓取模式: `category` 或 `keyword` |
| `category_fetch_days_ago` | int | **分类模式**: 获取过去 N 天的论文 (bioRxiv)。 |
| `max_papers_per_category_fetch` | int | **分类模式**: 每个 arXiv 分类最多获取的论文数。 |
| `biorxiv_days_ago` | int | **关键词模式**: 从 bioRxiv 获取过去 N 天的论文。 |
| `arxiv_max_results_kw` | int | **关键词模式**: 从 arXiv 获取的最大论文数量。 |
| `arxiv_sort_by` | string | **新增**: arXiv 排序方式。可选 `SubmittedDate`, `Relevance`, `LastUpdatedDate`。 |
| `search_by_authors` | list | **新增**: 作者列表，用于在 arXiv 和 bioRxiv 中进行筛选。 |
| `search_by_ids` | list | **新增**: arXiv ID 列表，用于精确查找。如果非空，将忽略其他所有筛选条件。 |

### `keywords`
一个字符串列表，仅在 **关键词模式** 下生效。

### `categories`
一个字典，定义了在 **分类模式** 下要抓取的具体类别。

---

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
    ├── main.py         # 命令行 (CLI) 入口
    ├── config.py       # 配置加载/保存模块
    ├── utils.py        # 辅助函数 (网络请求, 日志等)
    ├── database.py     # 数据库交互模块
    ├── crawler.py      # 核心抓取服务
    └── fetchers.py     # 各来源 (arXiv, bioRxiv) 的数据获取实现
```

## 📄 许可证
本项目采用 MIT 许可证。详情请见 `LICENSE` 文件。

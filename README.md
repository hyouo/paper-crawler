# 自动科研论文抓取脚本

这是一个 Python 脚本，用于自动从 [arXiv](https://arxiv.org/) 和 [bioRxiv](https://www.biorxiv.org/) 网站上抓取最新的科研论文。

## 主要功能

- **两种抓取模式**:
  1.  **关键词模式 (`keyword`)**: 根据预设的关键词列表（如 "systems biology", "medical ai" 等）搜索并下载相关论文。
  2.  **分类模式 (`category`)**: 从您感兴趣的 arXiv 和 bioRxiv 分类中抓取最新的论文。

- **下载与整理**:
  - 从 arXiv 下载的论文会以 PDF 格式直接保存。
  - 从 bioRxiv 找到的论文链接会整理成一个 Markdown 文件，方便查阅和访问。（因为有抓取墙，可能会有空了修复）
  - 所有文件都会自动保存在 `paper` 目录下，并按来源 (arXiv/bioRxiv) 和抓取日期进行归类。

- **配置**:
  - 您可以直接在 `main.py` 文件的头部轻松切换抓取模式。
  - 所有的关键词、学科分类、下载路径和抓取天数等都可以自定义。


## 如何使用

1.  **安装依赖**:
    脚本依赖 `requests` 库。您可以通过 pip 进行安装：
    ```bash
    pip install requests
    ```

2.  **配置脚本**:
    - 打开 `main.py` 文件。
    - 在文件头部的“用户配置”区域，根据您的需求进行修改：
      - 设置 `FETCH_METHOD` 为 `'keyword'` 或 `'category'`。
      - 如果使用关键词模式，请编辑 `KEYWORDS` 列表。
      - 如果使用分类模式，请编辑 `ARXIV_CATEGORIES` 和 `BIORXIV_CATEGORIES` 列表。
      - 您还可以调整其他参数，如抓取近几天的论文 (`CATEGORY_FETCH_DAYS_AGO`) 等。

3.  **运行脚本**:
    在项目根目录下，通过命令行运行脚本：
    ```bash
    python main.py
    ```

4.  **查看结果**:
    脚本运行完毕后，进入 `paper` 文件夹查看已下载的 PDF 文件和生成的 Markdown 链接列表。

## 项目结构

```
.
├── main.py             # 主脚本
├── paper/              # 存放抓取结果的目录
│   ├── arXiv/
│   │   └── 2025-09-01/
│   │       └── paper1.pdf
│   └── bioRxiv/
│       └── 2025-09-01/
│           └── links.md
├── README.md           # 本文档
└── .gitignore          # Git 忽略配置文件
```

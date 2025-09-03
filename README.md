# paper-crawler

轻量的科研论文抓取器，自动从 arXiv 与 bioRxiv 抓取论文并按来源与日期组织存储。

## 主要特点

- 支持两种抓取模式：`keyword`（关键词）与 `category`（分类）。
- arXiv 论文以 PDF 保存；bioRxiv 的结果会生成 Markdown 报告（可选包含摘要）。
- 配置集中在 `config.yaml`，无需修改代码即可调整行为。
- 现代化结构：代码位于 `src/`，支持通过命令行运行（CLI）。

## 快速开始

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 编辑配置：修改根目录下的 `config.yaml`（已经提供默认值）。

3. 运行（两种等效方式）：

```bash
# 直接运行 root 启动脚本（向下兼容）
python main.py --mode category

# 或作为模块运行（推荐）
python -m src.main --mode category
```

`--mode` 可选 `keyword` 或 `category`，会覆盖 `config.yaml` 中的 `fetch_settings.method`。

## 配置说明（`config.yaml`）

主要字段：

- `fetch_settings`：抓取相关参数（模式、时间范围、每类最大论文数等）。
- `output_settings.biorxiv_include_abstract_in_md`：是否在 bioRxiv 的 Markdown 报告中包含摘要。
- `keywords`：关键词模式下使用的关键词列表。
- `categories`：分类模式下的 arXiv 与 bioRxiv 分类列表。

示例：请参考仓库根目录的 `config.yaml`。

## 项目结构

```
.
├── config.yaml         # 可编辑的运行时配置
├── main.py             # 启动脚本（兼容旧习惯）
├── paper/              # 抓取结果（默认被 .gitignore 忽略）
├── requirements.txt
├── README.md
└── src/
  ├── __init__.py
  ├── main.py         # 现代入口，提供 CLI
  ├── config.py       # 加载 YAML 配置
  ├── utils.py        # 辅助函数（下载、网络、日志）
  └── fetchers.py     # 抓取实现（arXiv / bioRxiv）
```

## 开发者说明

- 日志通过 `logging` 控制，默认输出 INFO 级别。想看更多详细信息可在 `src/utils.py` 中修改 `setup_logging()`。
- `paper/` 文件夹默认被 `.gitignore` 忽略，以避免将大量二进制或大文件提交到仓库；如果你希望把生成的报告纳入版本管理，请修改 `.gitignore`。

## 运行示例

- 使用分类模式（配置文件或命令行）：

```bash
python -m src.main --mode category
```

- 使用关键词模式：

```bash
python -m src.main --mode keyword
```

## 许可证

请参见仓库根目录的 `LICENSE`。


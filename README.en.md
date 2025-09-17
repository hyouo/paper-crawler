# Paper Fetching and Management Platform

This is a refactored and feature-enhanced tool for fetching scientific papers.

![Web UI Screenshot](ui.png)

## ✨ Key Features

-   **Web UI**:
    -   **Preview Before Download**: The new workflow first fetches a list of paper metadata, allowing users to decide which papers to download after reading the abstracts.
    -   **Search Functionality**:
        -   Supports precise searching by **keywords**, **categories**, **authors**, and even a list of **arXiv IDs**.
        -   Customizable **sorting options** for arXiv results (by submission date, relevance, etc.).
-   **Command-Line Interface (CLI)**: Retains full CLI functionality, including interactive and direct execution modes, suitable for automation scripts.

## 🚀 Quick Start

### 1. Prerequisites
-   [Python 3.8+](https://www.python.org/)
-   (Optional) [Docker](https://www.docker.com/)

### 2. Install Dependencies
After cloning the project, run the following command in the root directory:
```bash
pip install -r requirements.txt
```
### 3. Choose How to Run

#### Option A: Web UI (Recommended)
This is the most common way to run this project.
```bash
python app.py
```
After the server starts, open your browser and navigate to [http://127.0.0.1:8080](http://127.0.0.1:8080).

**New UI Workflow**:
1.  In the left settings panel, select "By Category" or "By Keyword" mode.
2.  Expand "Advanced Settings" to configure authors, sorting options, and other parameters.
3.  Click the "Start Fetching" button.
4.  Once fetching is complete, the paper list will be displayed in the center panel.
5.  Click on any paper to view its detailed information (including the abstract) in the right panel.
6.  You can select multiple papers for "Batch Download," or in the right details panel, "Download this paper."
7.  After the download is complete, the "Open File" and "Open Folder" buttons will become available.

#### Option B: Command-Line Interface (CLI)
For automation scripts or users who prefer the terminal, the CLI provides powerful functionality.
```bash
# Start an interactive session
python -m src.main

# Directly fetch and download by keyword
python -m src.main --mode keyword
```

---

## 🌍 Language Switching

This project supports both English and Chinese.

-   **Web UI**: Click the `Language` dropdown menu in the top-right corner to switch languages in real-time.
-   **Command Line**:
    -   Start the tool with the `--lang` argument, e.g., `python -m src.main --lang en`.
    -   In interactive mode, if the language is not specified via an argument, you will be prompted to select a language first.

---

## ⚙️ Configuration (`config.yaml`)

You can modify most common settings directly in the Web UI, and these settings will be saved automatically to `config.yaml`.

### `fetch_settings`
Core parameters that control fetching behavior.

| Key                             | Type   | Description                                                                          |
| :------------------------------ | :----- | :----------------------------------------------------------------------------------- |
| `method`                        | string | Default fetch mode: `category` or `keyword`                                          |
| `category_fetch_days_ago`       | int    | **Category Mode**: Fetch papers from the last N days (bioRxiv).                      |
| `max_papers_per_category_fetch` | int    | **Category Mode**: Max number of papers to fetch per arXiv category.                 |
| `biorxiv_days_ago`              | int    | **Keyword Mode**: Fetch papers from the last N days from bioRxiv.                    |
| `arxiv_max_results_kw`          | int    | **Keyword Mode**: Max number of papers to fetch from arXiv.                          |
| `arxiv_sort_by`                 | string | **New**: arXiv sorting criteria. Options: `SubmittedDate`, `Relevance`, `LastUpdatedDate`. |
| `search_by_authors`             | list   | **New**: List of authors to filter by in arXiv and bioRxiv.                          |
| `search_by_ids`                 | list   | **New**: List of arXiv IDs for precise lookups. If not empty, all other filters are ignored. |

### `keywords`
A list of strings, effective only in **Keyword Mode**.

### `categories`
A dictionary defining the specific categories to fetch in **Category Mode**.

---

## 📁 Project Structure
```
.
├── app.py              # Web server entry point (Flask + SocketIO)
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration file
├── ui.png              # Web UI screenshot
├── paper/              # Default download directory for papers (.gitignore'd)
├── paper_crawler.db    # SQLite database file
├── templates/          # HTML template files
│   └── index.html
└── src/
    ├── __init__.py
    ├── main.py         # Command-line (CLI) entry point
    ├── config.py       # Config loading/saving module
    ├── utils.py        # Utility functions (networking, logging, etc.)
    ├── database.py     # Database interaction module
    ├── crawler.py      # Core crawling service
    └── fetchers.py     # Data fetching implementations (arXiv, bioRxiv)
```

## 📄 License
This project is licensed under the MIT License. See the `LICENSE` file for details.

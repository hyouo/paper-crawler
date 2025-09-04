# src/database.py

import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "paper_crawler.db")


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库和表"""
    if os.path.exists(DB_PATH):
        logger.info("数据库已存在，跳过初始化。")
        return

    logger.info("初始化数据库...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
        CREATE TABLE papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT,
            source TEXT NOT NULL, -- 'arXiv' or 'bioRxiv'
            category TEXT,
            paper_url TEXT UNIQUE NOT NULL, -- 论文摘要页链接
            pdf_url TEXT UNIQUE NOT NULL,   -- PDF下载链接
            filepath TEXT,                  -- 本地文件路径
            download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        )
        conn.commit()
        conn.close()
        logger.info("数据库表 'papers' 创建成功。")
    except sqlite3.Error as e:
        logger.error(f"数据库初始化失败: {e}")


def add_paper(paper_data):
    """添加一条论文记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
        INSERT INTO papers (title, authors, source, category, paper_url, pdf_url, filepath)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                paper_data.get("title", "N/A"),
                paper_data.get("authors"),
                paper_data.get("source"),
                paper_data.get("category"),
                paper_data.get("paper_url"),
                paper_data.get("pdf_url"),
                paper_data.get("filepath"),
            ),
        )
        conn.commit()
        conn.close()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logger.debug(
            f"论文 '{paper_data.get('title')}' 已存在，跳过添加。"
        )
        return None
    except sqlite3.Error as e:
        logger.error(f"添加论文到数据库失败: {e}")
        return None


def get_all_papers():
    """获取所有论文记录"""
    try:
        conn = get_db_connection()
        papers = conn.execute(
            "SELECT * FROM papers ORDER BY download_date DESC"
        ).fetchall()
        conn.close()
        return [dict(p) for p in papers]
    except sqlite3.Error as e:
        logger.error(f"从数据库获取论文列表失败: {e}")
        return []


def is_paper_downloaded(pdf_url):
    """通过 PDF 链接检查论文是否已下载"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM papers WHERE pdf_url = ?", (pdf_url,))
        paper = cursor.fetchone()
        conn.close()
        return paper is not None
    except sqlite3.Error as e:
        logger.error(f"查询数据库失败: {e}")
        return False


def delete_paper_by_id(paper_id):
    """通过ID删除单篇论文记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # First, get the filepath before deleting the record
        cursor.execute("SELECT filepath FROM papers WHERE id = ?", (paper_id,))
        result = cursor.fetchone()
        filepath = result["filepath"] if result else None

        cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
        conn.commit()
        conn.close()
        logger.info(f"成功从数据库删除论文 ID: {paper_id}")
        return filepath  # Return filepath for file system deletion
    except sqlite3.Error as e:
        logger.error(f"从数据库删除论文 ID: {paper_id} 失败: {e}")
        return None


def delete_papers_by_ids(paper_ids):
    """通过ID列表批量删除论文记录"""
    if not paper_ids:
        return []

    filepaths = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get filepaths for all papers to be deleted
        placeholders = ",".join("?" * len(paper_ids))
        cursor.execute(
            f"SELECT filepath FROM papers WHERE id IN ({placeholders})", paper_ids
        )
        results = cursor.fetchall()
        filepaths = [row["filepath"] for row in results if row["filepath"]]

        cursor.execute(f"DELETE FROM papers WHERE id IN ({placeholders})", paper_ids)
        conn.commit()
        conn.close()
        logger.info(f"成功从数据库批量删除论文 ID: {paper_ids}")
        return filepaths  # Return filepaths for file system deletion
    except sqlite3.Error as e:
        logger.error(f"从数据库批量删除论文 ID: {paper_ids} 失败: {e}")
        return []

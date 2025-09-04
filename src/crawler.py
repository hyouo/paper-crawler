# src/crawler.py

import os
import logging
from datetime import datetime
from threading import Thread

from . import fetchers, utils, database

logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, config, socketio=None):
        self.config = config
        self.socketio = socketio
        self.is_running = False
        self._stop_requested = False

    def _emit(self, event, data):
        if self.socketio:
            self.socketio.emit(event, data)
            # time.sleep(0.01) # Give the server a moment to send the message

    def start_crawl(self, mode, categories=None):
        if self.is_running:
            logger.warning("抓取任务已在运行中，请勿重复启动。")
            self._emit("status_update", {"status": "一个抓取任务已在运行中。"})
            return

        self._stop_requested = False
        self.is_running = True

        # 使用线程在后台运行抓取任务
        thread = Thread(target=self._run_crawl_task, args=(mode, categories))
        thread.start()

    def stop_crawl(self):
        if not self.is_running:
            logger.warning("没有正在运行的抓取任务。")
            return
        self._stop_requested = True
        logger.info("收到停止请求，将在当前论文处理完毕后停止。")
        self._emit("status_update", {"status": "收到停止请求..."})

    def _run_crawl_task(self, mode, categories):
        logger.info(f"抓取任务开始，模式: '{mode}', 类别: {categories}")
        self._emit("status_update", {"status": f"抓取任务启动，模式: '{mode}'"})

        try:
            # 1. 确定要调用的爬取函数和对应的类别列表
            arxiv_cats = []
            biorxiv_cats = []

            if categories and categories.get("chinese_arxiv"):
                arxiv_cats = categories["chinese_arxiv"]
            elif categories and categories.get("arxiv"):
                arxiv_cats = categories["arxiv"]

            if categories and categories.get("chinese_biorxiv"):
                biorxiv_cats = categories["chinese_biorxiv"]
            elif categories and categories.get("biorxiv"):
                biorxiv_cats = categories["biorxiv"]

            if mode == "keyword":
                fetcher_functions = [
                    (fetchers.fetch_from_arxiv_by_keyword, None),
                    (fetchers.fetch_from_biorxiv_by_keyword, None),
                ]
            elif mode == "category":
                fetcher_functions = [
                    (fetchers.fetch_from_arxiv_by_category, arxiv_cats),
                    (fetchers.fetch_from_biorxiv_by_category, biorxiv_cats),
                ]
            else:
                raise ValueError(f"未知的抓取模式: {mode}")

            # 2. 执行爬取并处理结果
            total_downloaded = 0
            for fetcher, cats_list in fetcher_functions:
                if self._stop_requested:
                    break

                source_name = fetcher.__name__.split("_")[2].capitalize()
                self._emit(
                    "status_update", {"status": f"正在从 {source_name} 获取论文列表..."}
                )

                # fetcher 将会是一个生成器，逐一产生论文信息
                if cats_list is not None:
                    paper_generator = fetcher(self.config, cats_list)
                else:
                    paper_generator = fetcher(self.config)

                papers_to_process = list(paper_generator)
                total_papers = len(papers_to_process)
                self._emit(
                    "status_update",
                    {
                        "status": f"从 {source_name} 找到 {total_papers} 篇论文。开始检查和下载..."
                    },
                )

                for i, paper_data in enumerate(papers_to_process):
                    if self._stop_requested:
                        logger.info("抓取任务已停止。")
                        break

                    self._emit(
                        "progress_update",
                        {
                            "source": source_name,
                            "progress": (
                                int(((i + 1) / total_papers) * 100)
                                if total_papers > 0
                                else 0
                            ),
                            "status": f"[{source_name}] 正在处理: {paper_data['title']:.50}...",
                        },
                    )

                    # 检查论文是否已下载
                    if database.is_paper_downloaded(paper_data["pdf_url"]):
                        logger.info(f"跳过已下载的论文: {paper_data['title']}")
                        continue

                    # 根据来源决定是否下载PDF
                    if paper_data["source"] == "bioRxiv":
                        logger.info(
                            f"跳过 bioRxiv 论文下载，只记录信息: {paper_data['title']}"
                        )
                        filepath = None  # bioRxiv 论文不下载，文件路径设为 None
                        paper_data["filepath"] = None  # 确保数据库中也记录为 None
                        # 存入数据库
                        database.add_paper(paper_data)
                        self._emit(
                            "paper_downloaded", {"paper": paper_data}
                        )  # 发送最新下载的论文信息
                    else:
                        filepath = self._download_paper(paper_data)
                        if filepath:
                            total_downloaded += 1
                            paper_data["filepath"] = filepath
                            # 存入数据库
                            database.add_paper(paper_data)
                            self._emit(
                                "paper_downloaded", {"paper": paper_data}
                            )  # 发送最新下载的论文信息

            final_status = (
                f"抓取任务完成。共下载 {total_downloaded} 篇新论文。"
                if not self._stop_requested
                else "抓取任务已手动停止。"
            )
            logger.info(final_status)
            self._emit("status_update", {"status": final_status})

        except Exception as e:
            logger.error(f"抓取任务执行失败: {e}", exc_info=True)
            self._emit("status_update", {"status": f"错误: {e}"})
        finally:
            self.is_running = False
            self._stop_requested = False
            self._emit("crawl_finished", {})

    def _download_paper(self, paper_data):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        today_str = datetime.now().strftime("%Y-%m-%d")
        download_dir = os.path.join(base_dir, "paper", paper_data["source"], today_str)
        os.makedirs(download_dir, exist_ok=True)

        filename = f"{utils.sanitize_filename(paper_data['title'])}.pdf"
        filepath = os.path.join(download_dir, filename)

        def progress_callback(progress, downloaded_mb, total_mb):
            self._emit(
                "download_progress",
                {
                    "filename": filename,
                    "progress": progress,
                },
            )

        if utils.download_pdf(
            paper_data["pdf_url"],
            filepath,
            paper_data.get("paper_url"),
            progress_callback,
        ):
            return filepath
        return None

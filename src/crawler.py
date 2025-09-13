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
            arxiv_cats = categories.get("arxiv", [])
            biorxiv_cats = categories.get("biorxiv", [])

            fetcher_map = {
                "keyword": [
                    (fetchers.fetch_from_arxiv_by_keyword, None),
                    (fetchers.fetch_from_biorxiv_by_keyword, None),
                ],
                "category": [
                    (fetchers.fetch_from_arxiv_by_category, arxiv_cats),
                    (fetchers.fetch_from_biorxiv_by_category, biorxiv_cats),
                ],
            }

            fetcher_functions = fetcher_map.get(mode)
            if not fetcher_functions:
                raise ValueError(f"未知的抓取模式: {mode}")

            # 2. 执行爬取并将所有结果收集到一个列表中
            paper_list = []
            unique_urls = set()

            for fetcher, cats_list in fetcher_functions:
                if self._stop_requested:
                    break

                source_name = fetcher.__name__.split("_")[2].capitalize()
                self._emit("status_update", {"status": f"正在从 {source_name} 获取论文列表..."})

                try:
                    # fetcher 是一个生成器
                    paper_generator = fetcher(self.config, cats_list) if cats_list is not None else fetcher(self.config)

                    for paper_data in paper_generator:
                        if self._stop_requested:
                            break
                        # 确保论文没有被重复添加
                        if paper_data["paper_url"] not in unique_urls:
                            # 检查论文是否已在数据库中
                            if not database.is_paper_downloaded(paper_data["pdf_url"]):
                                paper_list.append(paper_data)
                                unique_urls.add(paper_data["paper_url"])
                except Exception as e:
                    logger.error(f"从 {source_name} 获取数据时出错: {e}", exc_info=True)
                    self._emit("status_update", {"status": f"从 {source_name} 获取数据时出错: {e}"})

                if self._stop_requested:
                    break

            if self._stop_requested:
                final_status = "抓取任务已手动停止。"
            else:
                final_status = f"抓取任务完成。找到 {len(paper_list)} 篇新论文。"

            logger.info(final_status)
            self._emit("status_update", {"status": final_status})

            # 3. 将整个列表发送给前端，或者在CLI模式下返回它
            if self.socketio:
                self._emit("paper_list_update", {"papers": paper_list})
            else:
                return paper_list # CLI mode

        except Exception as e:
            logger.error(f"抓取任务执行失败: {e}", exc_info=True)
            self._emit("status_update", {"status": f"错误: {e}"})
        finally:
            self.is_running = False
            self._stop_requested = False
            self._emit("crawl_finished", {})

    def _download_paper(self, paper_data):
        """
        下载单个 PDF 文件并报告进度。
        这是一个私有方法，只负责下载，不与数据库交互。
        """
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
                    "pdf_url": paper_data["pdf_url"], # 使用唯一的 URL 作为标识符
                    "progress": progress,
                    "status": f"下载中... {downloaded_mb:.2f}/{total_mb:.2f} MB"
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

    def download_single_paper(self, paper_data):
        """
        公开方法：下载、更新数据库并通知前端。
        """
        try:
            logger.info(f"开始下载论文: {paper_data['title']}")

            # 检查是否已下载，以防万一
            if database.is_paper_downloaded(paper_data["pdf_url"]):
                logger.warning(f"论文 '{paper_data['title']}' 已存在于数据库中，跳过下载。")
                # 也许需要通知前端这个状态
                return

            filepath = self._download_paper(paper_data)

            if filepath:
                logger.info(f"论文 '{paper_data['title']}' 下载成功，路径: {filepath}")
                paper_data["filepath"] = filepath
                paper_data["download_date"] = datetime.now().isoformat()

                # 存入数据库
                database.add_paper(paper_data)

                # 通过 paper_downloaded 事件通知前端
                self._emit("paper_downloaded", {"paper": paper_data})
            else:
                logger.error(f"下载论文失败: {paper_data['title']}")
                self._emit("status_update", {"status": f"下载失败: {paper_data['title']}"})

        except Exception as e:
            logger.error(f"处理论文下载时出错 '{paper_data['title']}': {e}", exc_info=True)
            self._emit("status_update", {"status": f"处理下载时出错: {e}"})

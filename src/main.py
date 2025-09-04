# src/main.py

import argparse
import logging
import time

import argparse
import logging

from . import config
from .crawler import Crawler
from .database import init_db

logger = logging.getLogger(__name__)


def main():
    """
    主函数，程序的命令行入口点。
    """
    setup_logging()
    init_db()

    parser = argparse.ArgumentParser(description="自动科研论文抓取脚本 (命令行版)")
    parser.add_argument(
        "--config", type=str, default="config.yaml", help="配置文件的路径"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["keyword", "category"],
        help="覆盖配置文件中的抓取模式 ('keyword' 或 'category')",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(e)
        return

    # 命令行参数优先于配置文件
    fetch_method = (
        args.mode
        if args.mode
        else config.get("fetch_settings", {}).get("method", "category")
    )

    logger.info(f"命令行脚本启动，模式: '{fetch_method}'")

    # 命令行模式下不使用 socketio
    crawler = Crawler(config, socketio=None)

    # 直接调用内部的抓取任务函数，而不是通过线程
    # 注意：这将是一个阻塞操作
    crawler._run_crawl_task(fetch_method)

    logger.info(f"所有任务完成。请检查 'paper' 文件夹和数据库文件。")


if __name__ == "__main__":
    main()

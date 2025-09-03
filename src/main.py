import argparse
import logging
import os
from .config import load_config
from .utils import setup_logging
from .fetchers import (
    fetch_from_arxiv_by_keyword,
    fetch_from_biorxiv_by_keyword,
    fetch_from_arxiv_by_category,
    fetch_from_biorxiv_by_category
)

logger = logging.getLogger(__name__)

def main():
    """
    主函数，程序的入口点。
    """
    setup_logging()

    parser = argparse.ArgumentParser(description="自动科研论文抓取脚本")
    parser.add_argument(
        '--config', 
        type=str, 
        default='config.yaml', 
        help='配置文件的路径'
    )
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=['keyword', 'category'],
        help="覆盖配置文件中的抓取模式 ('keyword' 或 'category')"
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        logger.error(e)
        return

    # 命令行参数优先于配置文件
    fetch_method = args.mode if args.mode else config['fetch_settings']['method']
    
    # 设置下载目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 项目根目录
    config['base_download_dir'] = os.path.join(base_dir, 'paper')
    os.makedirs(config['base_download_dir'], exist_ok=True)

    logger.info(f"脚本启动，模式: '{fetch_method}'")
    
    if fetch_method == 'keyword':
        fetch_from_arxiv_by_keyword(config)
        fetch_from_biorxiv_by_keyword(config)
    elif fetch_method == 'category':
        fetch_from_arxiv_by_category(config)
        fetch_from_biorxiv_by_category(config)
    else:
        logger.error(f"未知的抓取模式: '{fetch_method}'. 请使用 'keyword' 或 'category'。")

    logger.info(f"所有任务完成。请检查 'paper' 文件夹。")

if __name__ == '__main__':
    main()

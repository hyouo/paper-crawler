import os
import re
import time
import logging
import requests

logger = logging.getLogger(__name__)

def setup_logging():
    """
    配置日志记录。
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def sanitize_filename(filename):
    """
    清理文件名，移除或替换Windows文件名中不支持的字符。
    """
    filename = re.sub(r'[\\/:*?"<>|]', '', filename)
    filename = filename.replace(':', ' ')
    filename = " ".join(filename.split())
    return filename[:150]

def make_api_request(url, max_retries=3, delay=5):
    """
    带有重试机制的网络请求函数。
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"API 请求失败 (尝试 {attempt + 1}/{max_retries})。 {delay}秒后重试...")
            logger.debug(f"错误详情: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    logger.error(f"连接 API 失败 {url} 经过 {max_retries} 次尝试。")
    return None

def download_pdf(url, filepath, referer=None):
    """
    下载单个PDF文件并显示进度。
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        }
        if referer:
            headers['Referer'] = referer

        response = requests.get(url, stream=True, timeout=30, headers=headers)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        logger.info(f"  正在下载: {os.path.basename(filepath)}")
        with open(filepath, 'wb') as f:
            downloaded_size = 0
            for data in response.iter_content(block_size):
                f.write(data)
                downloaded_size += len(data)
                done = int(50 * downloaded_size / total_size) if total_size > 0 else 0
                print(f"\r  [{'=' * done}{' ' * (50-done)}] {downloaded_size/1024/1024:.2f} MB", end='')
        print("\n  下载完成。")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"下载失败 {url}: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

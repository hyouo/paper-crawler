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
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def sanitize_filename(filename):
    """
    清理文件名，移除或替换Windows文件名中不支持的字符。
    """
    filename = re.sub(r'[\\/:*?"<>|]', "", filename)
    filename = filename.replace(":", " ")
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
            logger.warning(
                f"API 请求失败 (尝试 {attempt + 1}/{max_retries})。 {delay}秒后重试..."
            )
            logger.debug(f"错误详情: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    logger.error(f"连接 API 失败 {url} 经过 {max_retries} 次尝试。")
    return None


def download_pdf(
    url, filepath, referer=None, progress_callback=None, max_retries=3, delay=3
):
    """
    下载单个PDF文件并使用回调报告进度，带有重试机制。
    """
    for attempt in range(max_retries):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            if referer:
                headers["Referer"] = referer

            logger.debug(f"尝试下载 {url}, 尝试 {attempt + 1}/{max_retries}")
            response = requests.get(url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            logger.debug(f"下载请求成功，状态码: {response.status_code}")

            total_size = int(response.headers.get("content-length", 0))
            block_size = 1024

            filename = os.path.basename(filepath)
            logger.info(f"  开始下载: {filename}")

            downloaded_size = 0
            with open(filepath, "wb") as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    downloaded_size += len(data)
                    if total_size > 0 and progress_callback:
                        progress = int(100 * downloaded_size / total_size)
                        progress_callback(progress, downloaded_size, total_size)

            logger.info(f"  下载完成: {filename}")
            return True

        except requests.exceptions.HTTPError as e:
            logger.warning(
                f"下载失败 {url} (尝试 {attempt + 1}/{max_retries}) - HTTP 错误: {e.response.status_code}. 重试..."
            )
            if os.path.exists(filepath):
                os.remove(filepath)
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                logger.error(
                    f"下载失败 {url} 经过 {max_retries} 次尝试。最终 HTTP 错误: {e.response.status_code}."
                )
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"下载失败 {url} (尝试 {attempt + 1}/{max_retries}) - 请求错误: {e}. 重试..."
            )
            if os.path.exists(filepath):
                os.remove(filepath)
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                logger.error(
                    f"下载失败 {url} 经过 {max_retries} 次尝试。最终请求错误: {e}."
                )
                return False
    return False

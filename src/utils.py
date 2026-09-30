import os
import re
import time
import logging
import requests
import tempfile

logger = logging.getLogger(__name__)


from rich.logging import RichHandler

def setup_logging():
    """
    配置日志记录，使用 rich.logging 来美化输出。
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
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


def download_pdf(url, filepath, referer=None, progress_callback=None, max_retries=3, delay=3):
    """Publish only a complete PDF, without overwriting an existing download."""
    if os.path.lexists(filepath):
        logger.error("Download destination already exists: %s", filepath)
        return False
    for attempt in range(max_retries):
        temporary = None
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            if referer:
                headers["Referer"] = referer
            with requests.get(url, stream=True, timeout=30, headers=headers) as response:
                response.raise_for_status()
                try:
                    total_size = max(0, int(response.headers.get("content-length", 0)))
                except (TypeError, ValueError):
                    total_size = 0
                downloaded_size = 0
                signature = b""
                with tempfile.NamedTemporaryFile(mode="wb", delete=False,
                                                 dir=os.path.dirname(os.path.abspath(filepath)),
                                                 prefix=".download-", suffix=".part") as stream:
                    temporary = stream.name
                    for data in response.iter_content(64 * 1024):
                        if not data:
                            continue
                        signature = (signature + data)[:5]
                        stream.write(data)
                        downloaded_size += len(data)
                        if total_size and progress_callback:
                            progress_callback(min(100, int(100 * downloaded_size / total_size)),
                                              downloaded_size, total_size)
                    stream.flush()
                    os.fsync(stream.fileno())
                if signature != b"%PDF-":
                    raise ValueError("Download did not contain a PDF header.")
                if (total_size and response.headers.get("content-encoding", "identity") == "identity"
                        and downloaded_size != total_size):
                    raise ValueError("Download length does not match Content-Length.")
            # Same-directory hard link publishes atomically and fails if another
            # download has already created the destination. Never replace user data.
            os.link(temporary, filepath)
            logger.info("下载完成: %s", os.path.basename(filepath))
            return True
        except (requests.exceptions.RequestException, OSError, ValueError) as exc:
            logger.warning("下载失败 %s (尝试 %s/%s): %s", url, attempt + 1, max_retries, exc)
            if isinstance(exc, FileExistsError):
                return False
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
    return False

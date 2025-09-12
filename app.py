# app.py

# 使用 eventlet 进行 monkey-patching，以支持 Socket.IO 的异步特性
import eventlet
eventlet.monkey_patch()

import os
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO
import webbrowser
import threading

from src import config as cfg
from src import utils
from src import database
from src import fetchers
from src.crawler import Crawler

# --- 初始化 --- #

# 初始化日志
utils.setup_logging()
logger = logging.getLogger(__name__)

# 初始化数据库
database.init_db()

# 加载配置
config = cfg.load_config()

# 初始化 Flask 应用和 SocketIO
app = Flask(__name__)
app.config["SECRET_KEY"] = "your-very-secret-key-change-it!"  # 请在生产环境中更改此密钥
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
socketio = SocketIO(app, async_mode="eventlet")

# 初始化爬虫服务
crawler = Crawler(config, socketio)

# --- HTTP 路由 (REST API) --- #


@app.route("/")
def index():
    """渲染主页"""
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    """获取当前配置"""
    return jsonify(cfg.load_config())


@app.route("/api/config", methods=["POST"])
def set_config():
    """更新配置"""
    new_config = request.json
    # Ensure 'categories' and its sub-keys exist in new_config
    if "categories" not in new_config:
        new_config["categories"] = {}
    if "arxiv" not in new_config["categories"]:
        new_config["categories"]["arxiv"] = []
    if "biorxiv" not in new_config["categories"]:
        new_config["categories"]["biorxiv"] = []
    if "chinese_arxiv" not in new_config["categories"]:
        new_config["categories"]["chinese_arxiv"] = []
    if "chinese_biorxiv" not in new_config["categories"]:
        new_config["categories"]["chinese_biorxiv"] = []

    if cfg.save_config(new_config):
        # 更新爬虫实例中的配置
        crawler.config = new_config
        logger.info("配置已更新并重新加载到爬虫服务。")
        return jsonify({"status": "success", "message": "配置已成功保存。"})
    else:
        return jsonify({"status": "error", "message": "保存配置失败。"}), 500


@app.route("/api/papers", methods=["GET"])
def get_papers():
    """获取所有已下载论文的列表"""
    papers = database.get_all_papers()
    return jsonify(papers)


@app.route("/api/papers/delete", methods=["POST"])
def delete_papers():
    """删除指定的论文记录及其对应的PDF文件"""
    paper_ids = request.json.get("paper_ids", [])
    if not paper_ids:
        return jsonify({"status": "error", "message": "未提供论文ID。"}), 400

    try:
        # Delete from database and get filepaths
        deleted_filepaths = database.delete_papers_by_ids(paper_ids)

        # Delete actual PDF files
        deleted_count = 0
        for filepath in deleted_filepaths:
            if filepath:  # Ensure filepath is not None or empty
                full_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), filepath
                )
                if os.path.exists(full_path):
                    os.remove(full_path)
                    deleted_count += 1
                    logger.info(f"成功删除文件: {full_path}")
                else:
                    logger.warning(f"文件不存在，跳过删除: {full_path}")

        logger.info(
            f"成功删除 {len(paper_ids)} 条数据库记录，{deleted_count} 个文件被删除。"
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"成功删除 {len(paper_ids)} 条记录，{deleted_count} 文件。",
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"删除论文失败: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"删除论文失败: {e}"}), 500


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """
    Get a list of categories from arXiv and bioRxiv.
    """
    arxiv_categories = fetchers.get_arxiv_categories()
    biorxiv_categories = fetchers.get_biorxiv_categories()
    return jsonify({"arxiv": arxiv_categories, "biorxiv": biorxiv_categories})


@app.route("/paper_files/<path:filepath>")
def serve_paper_file(filepath):
    """提供对下载的PDF文件的访问"""
    # filepath 是从项目根目录开始的相对路径, e.g., "paper/arXiv/2023-10-27/some-paper.pdf"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # send_from_directory 需要一个绝对目录和一个文件名
    # 我们需要从 filepath 中分离出目录和文件名
    directory = os.path.join(base_dir, os.path.dirname(filepath))
    filename = os.path.basename(filepath)
    return send_from_directory(directory, filename)


# --- Socket.IO 事件处理 --- #


@socketio.on("connect")
def handle_connect():
    logger.info(f"客户端连接: {request.sid}")
    # 当客户端连接时，发送当前的运行状态
    if crawler.is_running:
        socketio.emit(
            "status_update", {"status": "一个抓取任务已在运行中。"}, room=request.sid
        )


@socketio.on("disconnect")
def handle_disconnect():
    logger.info(f"客户端断开连接: {request.sid}")


@socketio.on("start_crawl")
def handle_start_crawl(data):
    """处理开始抓取事件"""
    mode = data.get("mode", "category")
    categories = data.get("categories", {})
    logger.info(
        f"收到来自客户端 {request.sid} 的抓取请求，模式: {mode}, 类别: {categories}"
    )
    crawler.start_crawl(mode, categories)


@socketio.on("stop_crawl")
def handle_stop_crawl():
    """处理停止抓取事件"""
    logger.info(f"收到来自客户端 {request.sid} 的停止请求")
    crawler.stop_crawl()


# --- 主程序入口 --- #

if __name__ == "__main__":
    host = "127.0.0.1"  # Use 127.0.0.1 for local browser opening
    port = 8080
    url = f"http://{host}:{port}"
    logger.info(f"启动服务器，访问 {url}")

    # Open browser in a new thread to not block the server startup
    threading.Timer(1, lambda: webbrowser.open(url)).start()

    socketio.run(app, host=host, port=port)

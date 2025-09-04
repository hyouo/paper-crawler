import yaml
import os
import logging

logger = logging.getLogger(__name__)

# --- 路径处理 ---


def get_project_root() -> str:
    """获取项目的根目录路径。假定此脚本位于 src 目录下。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- 核心配置功能 ---


def load_config(config_path: str = None) -> dict:
    """
    加载 YAML 配置文件。
    如果 config_path 未提供，则默认加载项目根目录下的 'config.yaml'。
    """
    if config_path is None:
        config_path = os.path.join(get_project_root(), "config.yaml")

    if not os.path.exists(config_path):
        # 如果默认配置文件不存在，尝试创建一个
        if config_path == os.path.join(get_project_root(), "config.yaml"):
            logger.warning(f"配置文件 {config_path} 未找到，将创建一个默认配置。")
            default_config = {
                "fetch_settings": {
                    "arxiv_max_results_kw": 100,
                    "biorxiv_days_ago": 7,
                    "arxiv_max_results_cat": 50,  # Added this line
                    "category_fetch_days_ago": 7,  # Changed from 3 to 7
                },
                "keywords": ["machine learning", "bioinformatics"],
                "categories": {
                    "arxiv": ["cs.LG", "q-bio.QM"],
                    "biorxiv": ["bioinformatics", "genomics"],
                },
            }
            save_config(default_config, config_path)
            return default_config
        else:
            raise FileNotFoundError(f"指定的配置文件未找到: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"解析配置文件 {config_path} 出错: {e}")
        raise


def save_config(config_data: dict, config_path: str = None) -> bool:
    """
    保存配置数据到 YAML 文件。
    如果 config_path 未提供，则默认保存到项目根目录下的 'config.yaml'。
    """
    if config_path is None:
        config_path = os.path.join(get_project_root(), "config.yaml")

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                config_data,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        logger.info(f"配置已成功保存到 {config_path}")
        return True
    except Exception as e:
        logger.error(f"保存配置到 {config_path} 失败: {e}")
        return False

import yaml
import os

def load_config(config_path='config.yaml'):
    """
    加载 YAML 配置文件。
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件未找到: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

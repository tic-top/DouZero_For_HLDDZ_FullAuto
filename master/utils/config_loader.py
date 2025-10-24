"""
配置加载器 - 支持 YAML 配置文件和动态分辨率缩放
"""
import yaml
import os
from typing import Dict, Any, Tuple, List


class ConfigLoader:
    """配置加载和管理器"""

    def __init__(self, config_path: str = None):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径，默认为 config/default.yaml
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config",
                "default.yaml"
            )

        self.config_path = config_path
        self.config = self._load_config()
        self._current_resolution = None

    def _load_config(self) -> Dict[str, Any]:
        """加载 YAML 配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值（支持嵌套键）

        Args:
            key_path: 配置键路径，用 '.' 分隔，如 'game.window_class'
            default: 默认值

        Returns:
            配置值

        Example:
            >>> config.get('game.window_class')
            'UnityWndClass'
            >>> config.get('thresholds.bidding.call_landlord')
            0.2
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set_resolution(self, width: int, height: int):
        """
        设置当前分辨率，用于自动缩放坐标

        Args:
            width: 窗口宽度
            height: 窗口高度
        """
        self._current_resolution = (width, height)

    def get_region(self, region_name: str) -> Tuple[int, int, int, int]:
        """
        获取屏幕区域坐标（自动根据当前分辨率缩放）

        Args:
            region_name: 区域名称，如 'my_hand_cards'

        Returns:
            (x, y, width, height) 元组
        """
        base_region = self.get(f'regions.{region_name}')
        if base_region is None:
            raise ValueError(f"区域配置不存在: {region_name}")

        # 如果没有设置当前分辨率，返回基准坐标
        if self._current_resolution is None:
            return tuple(base_region)

        # 获取基准分辨率
        base_resolution = self.get('regions.base_resolution', [1440, 810])
        base_width, base_height = base_resolution
        curr_width, curr_height = self._current_resolution

        # 计算缩放比例
        scale_x = curr_width / base_width
        scale_y = curr_height / base_height

        # 缩放坐标
        x, y, w, h = base_region
        return (
            int(x * scale_x),
            int(y * scale_y),
            int(w * scale_x),
            int(h * scale_y)
        )

    def get_all_regions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """
        获取所有区域配置

        Returns:
            区域名称 -> 坐标的字典
        """
        regions = {}
        region_config = self.get('regions', {})

        for key, value in region_config.items():
            if key == 'base_resolution':
                continue
            if isinstance(value, list) and len(value) == 4:
                regions[key] = self.get_region(key)
            elif key == 'landlord_flags' and isinstance(value, list):
                # 特殊处理地主标志（多个位置）
                regions[key] = [self._scale_region(r) for r in value]

        return regions

    def _scale_region(self, region: List[int]) -> Tuple[int, int, int, int]:
        """内部方法：缩放单个区域"""
        if self._current_resolution is None:
            return tuple(region)

        base_resolution = self.get('regions.base_resolution', [1440, 810])
        base_width, base_height = base_resolution
        curr_width, curr_height = self._current_resolution

        scale_x = curr_width / base_width
        scale_y = curr_height / base_height

        x, y, w, h = region
        return (
            int(x * scale_x),
            int(y * scale_y),
            int(w * scale_x),
            int(h * scale_y)
        )

    def get_threshold(self, threshold_path: str) -> float:
        """
        获取 AI 决策阈值

        Args:
            threshold_path: 阈值路径，如 'bidding.call_landlord'

        Returns:
            阈值（浮点数）
        """
        return self.get(f'thresholds.{threshold_path}', 0.5)

    def get_model_path(self, model_type: str, position: str = None) -> str:
        """
        获取模型路径

        Args:
            model_type: 模型类型，如 'douzero', 'bidding', 'scoring'
            position: 位置（可选），如 'landlord', 'landlord_up'

        Returns:
            模型文件路径
        """
        if position:
            path = self.get(f'models.{model_type}.{position}')
        else:
            path = self.get(f'models.{model_type}.path')

        if path is None:
            raise ValueError(f"模型路径未配置: {model_type}.{position or 'path'}")

        # 转换为绝对路径
        if not os.path.isabs(path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            path = os.path.join(base_dir, path)

        return path

    def update(self, key_path: str, value: Any):
        """
        动态更新配置值

        Args:
            key_path: 配置键路径
            value: 新值
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self, path: str = None):
        """
        保存配置到文件

        Args:
            path: 保存路径，默认为原配置文件路径
        """
        save_path = path or self.config_path

        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)

    def __repr__(self):
        return f"ConfigLoader(config_path='{self.config_path}')"


# 全局配置实例（单例模式）
_global_config = None


def get_config(config_path: str = None) -> ConfigLoader:
    """
    获取全局配置实例

    Args:
        config_path: 配置文件路径（仅首次调用有效）

    Returns:
        ConfigLoader 实例
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigLoader(config_path)
    return _global_config

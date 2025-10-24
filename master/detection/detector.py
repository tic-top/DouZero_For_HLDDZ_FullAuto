"""
检测器基类 - 定义检测接口的抽象基类
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Any
from PIL import Image


class Detector(ABC):
    """
    检测器抽象基类

    所有检测器（卡牌检测、UI 检测等）都应继承此类
    """

    def __init__(self, config: Any):
        """
        初始化检测器

        Args:
            config: 配置对象
        """
        self.config = config
        self.confidence = config.get('detection.confidence', 0.8)

    @abstractmethod
    def detect(self, image: Image.Image, **kwargs) -> Optional[Any]:
        """
        执行检测

        Args:
            image: PIL Image 对象
            **kwargs: 其他参数

        Returns:
            检测结果，未检测到返回 None
        """
        pass

    def set_confidence(self, confidence: float):
        """
        设置检测置信度

        Args:
            confidence: 置信度阈值 (0.0-1.0)
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("置信度必须在 0.0 到 1.0 之间")
        self.confidence = confidence


class TemplateDetector(Detector):
    """
    模板匹配检测器

    使用 OpenCV 模板匹配算法检测图像中的目标
    """

    def __init__(self, config: Any):
        """初始化模板检测器"""
        super().__init__(config)
        self.templates = {}  # 模板缓存

    def load_template(self, name: str, template_path: str):
        """
        加载模板图像

        Args:
            name: 模板名称
            template_path: 模板图像路径
        """
        import cv2
        import numpy as np

        try:
            template = cv2.imread(template_path)
            if template is None:
                raise FileNotFoundError(f"模板文件不存在或无法读取: {template_path}")
            self.templates[name] = template
        except Exception as e:
            print(f"加载模板失败 {name}: {e}")

    def load_templates_from_dir(self, template_dir: str, pattern: str = "*.png"):
        """
        从目录加载所有模板

        Args:
            template_dir: 模板目录
            pattern: 文件匹配模式
        """
        import os
        import glob

        template_files = glob.glob(os.path.join(template_dir, pattern))
        for template_file in template_files:
            name = os.path.splitext(os.path.basename(template_file))[0]
            self.load_template(name, template_file)

        print(f"已加载 {len(template_files)} 个模板")

    def detect(
        self,
        image: Image.Image,
        template_name: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        **kwargs
    ) -> Optional[Tuple[int, int]]:
        """
        在图像中检测模板

        Args:
            image: PIL Image 对象
            template_name: 模板名称
            region: 搜索区域 (x, y, width, height)
            **kwargs: 其他参数

        Returns:
            匹配位置 (x, y)，未找到返回 None
        """
        import cv2
        import numpy as np

        # 检查模板是否已加载
        if template_name not in self.templates:
            print(f"警告: 模板 {template_name} 未加载")
            return None

        # PIL Image 转 OpenCV 格式
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_cv = img_array

        # 如果指定了区域，裁剪图像
        offset_x, offset_y = 0, 0
        if region:
            x, y, w, h = region
            img_cv = img_cv[y:y+h, x:x+w]
            offset_x, offset_y = x, y

        # 获取模板
        template = self.templates[template_name]

        # 模板匹配
        result = cv2.matchTemplate(img_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 检查置信度
        if max_val < self.confidence:
            return None

        # 返回匹配位置（加上偏移量）
        match_x = max_loc[0] + offset_x
        match_y = max_loc[1] + offset_y

        return (match_x, match_y)

    def detect_all(
        self,
        image: Image.Image,
        template_name: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        threshold: Optional[float] = None
    ) -> List[Tuple[int, int, float]]:
        """
        检测所有匹配位置

        Args:
            image: PIL Image 对象
            template_name: 模板名称
            region: 搜索区域
            threshold: 置信度阈值（可选）

        Returns:
            匹配位置列表 [(x, y, confidence), ...]
        """
        import cv2
        import numpy as np

        if template_name not in self.templates:
            return []

        # PIL Image 转 OpenCV
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_cv = img_array

        # 区域裁剪
        offset_x, offset_y = 0, 0
        if region:
            x, y, w, h = region
            img_cv = img_cv[y:y+h, x:x+w]
            offset_x, offset_y = x, y

        template = self.templates[template_name]
        result = cv2.matchTemplate(img_cv, template, cv2.TM_CCOEFF_NORMED)

        # 使用阈值
        conf_threshold = threshold if threshold is not None else self.confidence
        locations = np.where(result >= conf_threshold)

        matches = []
        for pt in zip(*locations[::-1]):
            match_x = pt[0] + offset_x
            match_y = pt[1] + offset_y
            confidence = result[pt[1], pt[0]]
            matches.append((match_x, match_y, float(confidence)))

        return matches


class CardDetector(TemplateDetector):
    """
    卡牌检测器

    专门用于检测斗地主卡牌的检测器
    """

    # 卡牌类型（从大到小）
    CARD_TYPES = ['D', 'X', '2', 'A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3']

    def __init__(self, config: Any):
        """初始化卡牌检测器"""
        super().__init__(config)

        # 加载卡牌模板
        self._load_card_templates()

    def _load_card_templates(self):
        """加载所有卡牌模板"""
        import os

        templates_base = self.config.get('templates.base_path', '../pics')
        base_dir = os.path.dirname(os.path.dirname(__file__))
        templates_dir = os.path.join(base_dir, templates_base)

        # 加载不同前缀的卡牌模板
        prefixes = {
            'my': self.config.get('templates.my_cards', 'm'),
            'other': self.config.get('templates.other_cards', 'o'),
            'center': self.config.get('templates.center_cards', 'c'),
            'bottom': self.config.get('templates.bottom_cards', 'z'),
        }

        for prefix_name, prefix in prefixes.items():
            for card in self.CARD_TYPES:
                template_name = f"{prefix}{card}"
                template_path = os.path.join(templates_dir, f"{template_name}.png")

                if os.path.exists(template_path):
                    self.load_template(template_name, template_path)

    def detect_cards(
        self,
        image: Image.Image,
        card_type: str = 'my',
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> List[str]:
        """
        检测图像中的卡牌

        Args:
            image: PIL Image 对象
            card_type: 卡牌类型 ('my', 'other', 'center', 'bottom')
            region: 搜索区域

        Returns:
            卡牌列表，如 ['D', 'X', '2', '2', 'A']
        """
        # 获取模板前缀
        prefix_map = {
            'my': self.config.get('templates.my_cards', 'm'),
            'other': self.config.get('templates.other_cards', 'o'),
            'center': self.config.get('templates.center_cards', 'c'),
            'bottom': self.config.get('templates.bottom_cards', 'z'),
        }
        prefix = prefix_map.get(card_type, 'm')

        detected_cards = []

        # 遍历所有卡牌类型
        for card in self.CARD_TYPES:
            template_name = f"{prefix}{card}"

            # 检测所有匹配
            matches = self.detect_all(image, template_name, region)

            # 添加到结果
            for match in matches:
                detected_cards.append((card, match[0], match[1], match[2]))

        # 按 x 坐标排序（从左到右）
        detected_cards.sort(key=lambda x: x[1])

        # 过滤重复（如果两张牌的位置太接近，只保留置信度高的）
        filtered_cards = self._filter_duplicates(detected_cards)

        # 只返回卡牌类型
        return [card[0] for card in filtered_cards]

    def _filter_duplicates(
        self,
        cards: List[Tuple[str, int, int, float]],
        min_distance: int = 20
    ) -> List[Tuple[str, int, int, float]]:
        """
        过滤重复检测的卡牌

        Args:
            cards: 卡牌列表 [(card, x, y, confidence), ...]
            min_distance: 最小距离（像素）

        Returns:
            过滤后的卡牌列表
        """
        if not cards:
            return []

        filtered = []
        for card in cards:
            card_type, x, y, conf = card

            # 检查是否与已有卡牌太接近
            is_duplicate = False
            for existing in filtered:
                ex_type, ex_x, ex_y, ex_conf = existing
                distance = ((x - ex_x) ** 2 + (y - ex_y) ** 2) ** 0.5

                if distance < min_distance:
                    # 如果太接近，保留置信度高的
                    if conf > ex_conf:
                        filtered.remove(existing)
                    else:
                        is_duplicate = True
                    break

            if not is_duplicate:
                filtered.append(card)

        return filtered

    def detect(self, image: Image.Image, **kwargs) -> List[str]:
        """
        实现抽象方法：检测卡牌

        Args:
            image: PIL Image
            **kwargs: 可选参数（card_type, region）

        Returns:
            卡牌列表
        """
        card_type = kwargs.get('card_type', 'my')
        region = kwargs.get('region', None)
        return self.detect_cards(image, card_type, region)

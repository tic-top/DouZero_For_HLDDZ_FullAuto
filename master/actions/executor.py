"""
动作执行器 - 执行游戏中的各种操作（点击、选牌等）
"""
import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import win32gui
import win32api
import win32con


class ActionExecutor(ABC):
    """动作执行器抽象基类"""

    def __init__(self, config):
        """
        初始化执行器

        Args:
            config: 配置对象
        """
        self.config = config
        self.click_delay = config.get('actions.click_delay', 0.05)
        self.animation_wait = config.get('actions.animation_wait', 0.3)

    @abstractmethod
    def execute(self, **kwargs):
        """执行动作"""
        pass

    def wait(self, duration: float = None):
        """等待一段时间"""
        time.sleep(duration or self.click_delay)


class MouseExecutor(ActionExecutor):
    """
    鼠标操作执行器

    使用 win32api 进行鼠标点击、移动等操作
    """

    def __init__(self, config, window_handle: int = None):
        """
        初始化鼠标执行器

        Args:
            config: 配置对象
            window_handle: 游戏窗口句柄
        """
        super().__init__(config)
        self.hwnd = window_handle

    def set_window_handle(self, hwnd: int):
        """设置窗口句柄"""
        self.hwnd = hwnd

    def click(self, x: int, y: int, relative: bool = False):
        """
        点击指定位置

        Args:
            x: X 坐标
            y: Y 坐标
            relative: 是否为相对于窗口的坐标
        """
        if self.hwnd and relative:
            # 转换为屏幕坐标
            rect = win32gui.GetWindowRect(self.hwnd)
            x += rect[0]
            y += rect[1]

        # 发送鼠标点击
        win32api.SetCursorPos((x, y))
        time.sleep(self.click_delay)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(self.click_delay)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(self.click_delay)

    def click_window(self, x: int, y: int):
        """
        在窗口内点击（使用 SendMessage）

        Args:
            x: 窗口相对 X 坐标
            y: 窗口相对 Y 坐标
        """
        if not self.hwnd:
            raise ValueError("未设置窗口句柄")

        lParam = y << 16 | x
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        time.sleep(self.click_delay)
        win32gui.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)
        time.sleep(self.click_delay)

    def move_to(self, x: int, y: int):
        """移动鼠标到指定位置"""
        win32api.SetCursorPos((x, y))

    def execute(self, x: int, y: int, method: str = 'api', **kwargs):
        """
        执行点击动作

        Args:
            x: X 坐标
            y: Y 坐标
            method: 点击方法 ('api' 或 'message')
            **kwargs: 其他参数
        """
        if method == 'message':
            self.click_window(x, y)
        else:
            relative = kwargs.get('relative', False)
            self.click(x, y, relative)


class CardSelector(ActionExecutor):
    """
    卡牌选择器

    负责在游戏中选择和点击卡牌
    """

    def __init__(self, config, mouse_executor: MouseExecutor):
        """
        初始化卡牌选择器

        Args:
            config: 配置对象
            mouse_executor: 鼠标执行器
        """
        super().__init__(config)
        self.mouse = mouse_executor
        self.card_spacing = config.get('detection.card_spacing', 45.6)
        self.verification_enabled = config.get('actions.verification_enabled', True)

    def select_cards(
        self,
        my_cards: List[str],
        cards_to_play: List[str],
        hand_region: Tuple[int, int, int, int]
    ) -> bool:
        """
        选择要出的卡牌

        Args:
            my_cards: 当前手牌（从左到右）
            cards_to_play: 要选择的卡牌
            hand_region: 手牌区域 (x, y, width, height)

        Returns:
            是否选择成功
        """
        if not cards_to_play:
            return True  # 不出牌（过牌）

        try:
            # 计算卡牌位置
            card_positions = self._calculate_card_positions(my_cards, hand_region)

            # 创建卡牌到位置的映射（处理重复卡牌）
            card_index_map = self._create_card_index_map(my_cards)

            # 点击要出的每张牌
            used_indices = set()
            for card in cards_to_play:
                if card not in card_index_map:
                    print(f"警告: 卡牌 {card} 不在手牌中")
                    return False

                # 找到未使用的该卡牌索引
                indices = [idx for idx in card_index_map[card] if idx not in used_indices]
                if not indices:
                    print(f"警告: 卡牌 {card} 数量不足")
                    return False

                # 选择第一个可用的索引
                index = indices[0]
                used_indices.add(index)

                # 点击卡牌
                x, y = card_positions[index]
                self.mouse.click(x, y, relative=True)
                self.wait()

            # 验证选择（可选）
            if self.verification_enabled:
                # 这里可以添加验证逻辑，检查卡牌是否正确选中
                pass

            return True

        except Exception as e:
            print(f"卡牌选择失败: {e}")
            return False

    def click_play_button(self, button_region: Tuple[int, int, int, int]):
        """
        点击"出牌"按钮

        Args:
            button_region: 按钮区域
        """
        x, y, w, h = button_region
        # 点击区域中心
        center_x = x + w // 2
        center_y = y + h // 2
        self.mouse.click(center_x, center_y, relative=True)
        self.wait(self.animation_wait)

    def click_pass_button(self, button_region: Tuple[int, int, int, int]):
        """
        点击"不要"/"过"按钮

        Args:
            button_region: 按钮区域
        """
        self.click_play_button(button_region)

    def _calculate_card_positions(
        self,
        cards: List[str],
        region: Tuple[int, int, int, int]
    ) -> List[Tuple[int, int]]:
        """
        计算每张卡牌的位置

        Args:
            cards: 卡牌列表
            region: 手牌区域

        Returns:
            位置列表 [(x, y), ...]
        """
        x, y, w, h = region

        # 计算起始位置（通常需要找到"左上角"标记）
        # 这里简化处理，假设从区域左侧开始
        start_x = x + 50  # 左侧偏移
        start_y = y + h // 2  # 中心高度

        positions = []
        for i in range(len(cards)):
            card_x = int(start_x + i * self.card_spacing)
            card_y = start_y
            positions.append((card_x, card_y))

        return positions

    def _create_card_index_map(self, cards: List[str]) -> dict:
        """
        创建卡牌到索引的映射（处理重复卡牌）

        Args:
            cards: 卡牌列表

        Returns:
            字典，card -> [index1, index2, ...]
        """
        card_map = {}
        for i, card in enumerate(cards):
            if card not in card_map:
                card_map[card] = []
            card_map[card].append(i)
        return card_map

    def execute(
        self,
        action: str,
        my_cards: List[str] = None,
        cards_to_play: List[str] = None,
        **kwargs
    ):
        """
        执行卡牌动作

        Args:
            action: 动作类型 ('select', 'play', 'pass')
            my_cards: 当前手牌
            cards_to_play: 要出的牌
            **kwargs: 其他参数
        """
        if action == 'select':
            hand_region = kwargs.get('hand_region') or self.config.get_region('my_hand_cards')
            return self.select_cards(my_cards, cards_to_play, hand_region)

        elif action == 'play':
            button_region = kwargs.get('button_region') or self.config.get_region('general_button')
            self.click_play_button(button_region)

        elif action == 'pass':
            button_region = kwargs.get('button_region') or self.config.get_region('pass_button')
            self.click_pass_button(button_region)


class BidExecutor(ActionExecutor):
    """
    叫地主/加倍操作执行器
    """

    def __init__(self, config, mouse_executor: MouseExecutor):
        """初始化叫地主执行器"""
        super().__init__(config)
        self.mouse = mouse_executor

    def call_landlord(self):
        """点击"叫地主"按钮"""
        # 这里需要根据实际按钮位置点击
        # 简化处理
        button_region = self.config.get_region('general_button')
        x, y, w, h = button_region
        self.mouse.click(x + w // 3, y + h // 2, relative=True)
        self.wait(self.animation_wait)

    def pass_landlord(self):
        """点击"不叫"按钮"""
        button_region = self.config.get_region('general_button')
        x, y, w, h = button_region
        self.mouse.click(x + 2 * w // 3, y + h // 2, relative=True)
        self.wait(self.animation_wait)

    def double(self, level: int = 2):
        """
        加倍

        Args:
            level: 加倍等级 (1=不加倍, 2=加倍, 3=超级加倍)
        """
        if level == 1:
            return  # 不加倍

        button_region = self.config.get_region('general_button')
        x, y, w, h = button_region

        if level == 2:
            # 加倍按钮（通常在左侧）
            self.mouse.click(x + w // 3, y + h // 2, relative=True)
        elif level == 3:
            # 超级加倍（通常在中间）
            self.mouse.click(x + w // 2, y + h // 2, relative=True)

        self.wait(self.animation_wait)

    def execute(self, action: str, **kwargs):
        """
        执行叫地主/加倍动作

        Args:
            action: 动作类型 ('call', 'pass', 'double')
            **kwargs: 其他参数
        """
        if action == 'call':
            self.call_landlord()
        elif action == 'pass':
            self.pass_landlord()
        elif action == 'double':
            level = kwargs.get('level', 2)
            self.double(level)


# 使用示例
if __name__ == "__main__":
    from master.utils import get_config

    config = get_config()

    # 创建鼠标执行器
    mouse = MouseExecutor(config)

    # 创建卡牌选择器
    selector = CardSelector(config, mouse)

    # 测试卡牌选择
    my_cards = ['D', 'X', '2', '2', 'A', 'K', 'Q', 'J']
    cards_to_play = ['2', '2']
    hand_region = (180, 560, 1050, 90)

    print(f"选择卡牌: {cards_to_play}")
    # selector.select_cards(my_cards, cards_to_play, hand_region)

"""
AI Agent 抽象基类 - 定义决策接口
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DecisionResult:
    """
    决策结果

    Attributes:
        action: 推荐的动作（卡牌组合），如 ['3', '3'] 或 []（表示过牌）
        confidence: 置信度 (0.0-1.0)
        alternatives: 备选方案列表 [(action, confidence), ...]
        reasoning: 决策理由（可选）
    """
    action: List[str]
    confidence: float
    alternatives: List[Tuple[List[str], float]] = None
    reasoning: str = None

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


@dataclass
class BidDecision:
    """
    叫地主决策结果

    Attributes:
        should_bid: 是否叫地主
        score: 评分（用于比较）
        confidence: 置信度
    """
    should_bid: bool
    score: float
    confidence: float


@dataclass
class DoubleDecision:
    """
    加倍决策结果

    Attributes:
        should_double: 是否加倍
        level: 加倍等级（1=不加倍, 2=加倍, 3=超级加倍）
        score: 评分
        confidence: 置信度
    """
    should_double: bool
    level: int  # 1, 2, 3
    score: float
    confidence: float


class Agent(ABC):
    """
    AI Agent 抽象基类

    所有 AI agent（DouZero, 规则based, 混合等）都应实现此接口
    """

    def __init__(self, config: Any, position: str):
        """
        初始化 Agent

        Args:
            config: 配置对象
            position: 玩家位置 ('landlord', 'landlord_up', 'landlord_down')
        """
        self.config = config
        self.position = position

    @abstractmethod
    def decide_action(
        self,
        my_cards: List[str],
        played_cards: List[str],
        game_state: Dict[str, Any]
    ) -> DecisionResult:
        """
        决定出牌动作

        Args:
            my_cards: 我的手牌，如 ['D', 'X', '2', '2', 'A', 'K']
            played_cards: 上一手牌，如 ['K', 'K'] 或 []（表示可以任意出）
            game_state: 游戏状态信息

        Returns:
            DecisionResult 对象
        """
        pass

    @abstractmethod
    def decide_bid(self, initial_cards: List[str]) -> BidDecision:
        """
        决定是否叫地主

        Args:
            initial_cards: 初始手牌（通常是前几张牌）

        Returns:
            BidDecision 对象
        """
        pass

    @abstractmethod
    def decide_double(
        self,
        my_cards: List[str],
        position: str,
        landlord_cards: Optional[List[str]] = None
    ) -> DoubleDecision:
        """
        决定是否加倍

        Args:
            my_cards: 我的手牌
            position: 我的位置
            landlord_cards: 地主底牌（可选）

        Returns:
            DoubleDecision 对象
        """
        pass

    def reset(self):
        """重置 agent 状态（可选实现）"""
        pass


class RuleBasedAgent(Agent):
    """
    基于规则的 Agent（简单实现，用于备用或教学）
    """

    def decide_action(
        self,
        my_cards: List[str],
        played_cards: List[str],
        game_state: Dict[str, Any]
    ) -> DecisionResult:
        """简单规则：出最小的牌"""
        if not my_cards:
            return DecisionResult(action=[], confidence=0.0)

        # 如果可以任意出，出单张最小的牌
        if not played_cards:
            smallest_card = min(my_cards, key=self._card_value)
            return DecisionResult(
                action=[smallest_card],
                confidence=0.5,
                reasoning="出最小的单牌"
            )

        # 否则尝试找能压过的最小牌
        # 这里简化处理，实际需要复杂的牌型判断
        return DecisionResult(
            action=[],
            confidence=0.3,
            reasoning="简单规则：选择过牌"
        )

    def decide_bid(self, initial_cards: List[str]) -> BidDecision:
        """简单规则：根据大牌数量决定"""
        big_cards = [c for c in initial_cards if c in ['D', 'X', '2', 'A']]
        score = len(big_cards) / len(initial_cards) if initial_cards else 0

        return BidDecision(
            should_bid=score > 0.3,
            score=score,
            confidence=0.5
        )

    def decide_double(
        self,
        my_cards: List[str],
        position: str,
        landlord_cards: Optional[List[str]] = None
    ) -> DoubleDecision:
        """简单规则：根据手牌质量决定"""
        big_cards = [c for c in my_cards if c in ['D', 'X', '2', 'A']]
        score = len(big_cards) / len(my_cards) if my_cards else 0

        return DoubleDecision(
            should_double=score > 0.4,
            level=2 if score > 0.4 else 1,
            score=score,
            confidence=0.5
        )

    @staticmethod
    def _card_value(card: str) -> int:
        """卡牌数值"""
        values = {
            '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14, '2': 15, 'X': 16, 'D': 17
        }
        return values.get(card, 0)


# 使用示例
if __name__ == "__main__":
    from master.utils import get_config

    # 创建配置
    config = get_config()

    # 创建规则 agent
    agent = RuleBasedAgent(config, 'landlord')

    # 测试叫地主决策
    initial_cards = ['D', 'X', '2', 'A', 'K', 'Q']
    bid_result = agent.decide_bid(initial_cards)
    print(f"叫地主决策: {bid_result}")

    # 测试出牌决策
    my_cards = ['2', '2', 'A', 'K', 'Q', 'J', 'T', '9', '8', '7']
    played_cards = []
    action_result = agent.decide_action(my_cards, played_cards, {})
    print(f"出牌决策: {action_result}")

    # 测试加倍决策
    double_result = agent.decide_double(my_cards, 'landlord')
    print(f"加倍决策: {double_result}")

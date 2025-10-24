"""
DouZero Agent - 基于深度学习的 AI 决策
"""
import sys
import os

# 添加父目录到路径，以便导入 douzero 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import List, Dict, Any, Optional
from master.core.agent import Agent, DecisionResult, BidDecision, DoubleDecision

# 导入原有的 DouZero 模块
try:
    from douzero.evaluation.deep_agent import DeepAgent
    from douzero.env.game import GameEnv
    import BidModel
    import LandlordModel
    import FarmerModel
except ImportError as e:
    print(f"警告: 无法导入 DouZero 模块: {e}")
    DeepAgent = None
    GameEnv = None


class DouZeroAgent(Agent):
    """
    DouZero AI Agent

    封装 DouZero 深度学习模型，提供统一的决策接口
    """

    # 卡牌映射
    ENV_CARD_MAP = {
        3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9',
        10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A', 17: '2',
        20: 'X', 30: 'D'
    }

    REAL_CARD_MAP = {v: k for k, v in ENV_CARD_MAP.items()}

    def __init__(self, config: Any, position: str):
        """
        初始化 DouZero Agent

        Args:
            config: 配置对象
            position: 玩家位置
        """
        super().__init__(config, position)

        if DeepAgent is None or GameEnv is None:
            raise ImportError("DouZero 模块未正确导入，无法使用 DouZeroAgent")

        # 加载模型
        model_path = config.get_model_path('douzero', position)
        self.deep_agent = DeepAgent(position, model_path)

        # 创建游戏环境（用于状态管理）
        self.env = GameEnv([self.deep_agent])

        # 加载评分模型
        self._load_scoring_models()

        print(f"DouZeroAgent 已初始化 (position={position}, model={model_path})")

    def _load_scoring_models(self):
        """加载叫地主和加倍评分模型"""
        try:
            # 叫地主模型
            bid_model_path = self.config.get_model_path('bidding', None)
            BidModel.BidModel(bid_model_path, True, self.config.get('detection.card_spacing', 45.6))

            # 根据位置加载对应的评分模型
            if self.position == 'landlord':
                landlord_path = self.config.get_model_path('scoring', 'landlord')
                LandlordModel.init_model(landlord_path)
            else:
                farmer_path = self.config.get_model_path('scoring', 'farmer')
                FarmerModel.init_model(farmer_path)

                # 同时加载其他位置的模型
                for pos in ['landlord_up', 'landlord_down']:
                    if pos != self.position:
                        path = self.config.get_model_path('douzero', pos)
                        # 预加载模型（可选）

        except Exception as e:
            print(f"警告: 评分模型加载失败: {e}")

    def decide_action(
        self,
        my_cards: List[str],
        played_cards: List[str],
        game_state: Dict[str, Any]
    ) -> DecisionResult:
        """
        决定出牌动作

        Args:
            my_cards: 我的手牌
            played_cards: 上一手牌
            game_state: 游戏状态（需要包含 infoset）

        Returns:
            DecisionResult 对象
        """
        try:
            # 从 game_state 获取 infoset
            infoset = game_state.get('infoset')
            if infoset is None:
                raise ValueError("game_state 必须包含 'infoset'")

            # 使用 DouZero 模型决策
            action, confidence, action_list = self.deep_agent.act(infoset)

            # 转换动作格式（环境编码 -> 真实卡牌）
            action_cards = self._env_to_real_cards(action)

            # 转换备选方案
            alternatives = []
            for alt_action, alt_conf in action_list[:5]:  # 取前5个备选
                alt_cards = self._env_to_real_cards(alt_action)
                alternatives.append((alt_cards, float(alt_conf)))

            return DecisionResult(
                action=action_cards,
                confidence=float(confidence),
                alternatives=alternatives,
                reasoning=f"DouZero 推荐 (置信度={confidence:.3f})"
            )

        except Exception as e:
            print(f"DouZero 决策失败: {e}")
            # 返回过牌
            return DecisionResult(
                action=[],
                confidence=0.0,
                reasoning=f"决策失败: {e}"
            )

    def decide_bid(self, initial_cards: List[str]) -> BidDecision:
        """
        决定是否叫地主

        Args:
            initial_cards: 初始手牌（前几张）

        Returns:
            BidDecision 对象
        """
        try:
            # 转换卡牌格式
            env_cards = self._real_to_env_cards(initial_cards)

            # 使用 BidModel 评分
            score = BidModel.predict(env_cards)

            # 获取阈值
            threshold = self.config.get_threshold('bidding.call_landlord')

            return BidDecision(
                should_bid=score > threshold,
                score=float(score),
                confidence=float(abs(score - threshold))
            )

        except Exception as e:
            print(f"叫地主决策失败: {e}")
            return BidDecision(should_bid=False, score=0.0, confidence=0.0)

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
            landlord_cards: 地主底牌

        Returns:
            DoubleDecision 对象
        """
        try:
            # 转换卡牌
            env_my_cards = self._real_to_env_cards(my_cards)
            env_landlord_cards = self._real_to_env_cards(landlord_cards) if landlord_cards else []

            # 根据位置选择模型
            if position == 'landlord':
                score = LandlordModel.predict(env_my_cards)
                # 获取地主加倍阈值
                threshold = self.config.get_threshold('doubling.landlord_not_stole_1')
            else:
                score = FarmerModel.predict_env(env_my_cards, env_landlord_cards)
                # 获取农民加倍阈值
                threshold = self.config.get_threshold('doubling.farmer_high')

            # 决定加倍等级
            should_double = score > threshold
            level = 2 if should_double else 1  # 简化：2=加倍，1=不加倍

            return DoubleDecision(
                should_double=should_double,
                level=level,
                score=float(score),
                confidence=float(abs(score - threshold))
            )

        except Exception as e:
            print(f"加倍决策失败: {e}")
            return DoubleDecision(should_double=False, level=1, score=0.0, confidence=0.0)

    def _real_to_env_cards(self, cards: List[str]) -> List[int]:
        """
        真实卡牌转换为环境编码

        Args:
            cards: 真实卡牌，如 ['D', 'X', '2', 'A']

        Returns:
            环境编码，如 [30, 20, 17, 14]
        """
        return [self.REAL_CARD_MAP.get(card, 0) for card in cards]

    def _env_to_real_cards(self, env_cards: List[int]) -> List[str]:
        """
        环境编码转换为真实卡牌

        Args:
            env_cards: 环境编码

        Returns:
            真实卡牌
        """
        return [self.ENV_CARD_MAP.get(card, '') for card in env_cards]

    def reset(self):
        """重置环境状态"""
        self.env = GameEnv([self.deep_agent])


# 使用示例
if __name__ == "__main__":
    from master.utils import get_config

    # 创建配置
    config = get_config()

    # 创建 DouZero agent
    try:
        agent = DouZeroAgent(config, 'landlord')
        print("DouZero Agent 创建成功")

        # 测试叫地主
        initial_cards = ['D', 'X', '2', 'A', 'K', 'Q']
        bid_result = agent.decide_bid(initial_cards)
        print(f"叫地主决策: {bid_result}")

        # 测试加倍
        my_cards = ['2', '2', 'A', 'K', 'Q', 'J', 'T', '9', '8', '7']
        double_result = agent.decide_double(my_cards, 'landlord')
        print(f"加倍决策: {double_result}")

    except Exception as e:
        print(f"测试失败: {e}")

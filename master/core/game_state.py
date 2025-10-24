"""
游戏状态管理器 - 清晰的状态机模式
"""
from enum import Enum, auto
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


class GamePhase(Enum):
    """游戏阶段枚举"""
    IDLE = auto()              # 空闲（未开始）
    WAITING_START = auto()     # 等待开始
    BIDDING = auto()           # 叫地主阶段
    DOUBLING = auto()          # 加倍阶段
    CARD_PLAYING = auto()      # 出牌阶段
    GAME_OVER = auto()         # 游戏结束


class PlayerPosition(Enum):
    """玩家位置枚举"""
    LANDLORD = "landlord"           # 地主
    LANDLORD_UP = "landlord_up"     # 地主上家（农民）
    LANDLORD_DOWN = "landlord_down" # 地主下家（农民）
    UNKNOWN = "unknown"              # 未知


@dataclass
class CardState:
    """卡牌状态"""
    my_cards: List[str] = field(default_factory=list)           # 我的手牌
    landlord_cards: List[str] = field(default_factory=list)     # 地主底牌
    played_cards: Dict[str, List[str]] = field(default_factory=dict)  # 已出的牌
    last_played: Optional[List[str]] = None                     # 上一手牌
    last_player: Optional[str] = None                           # 上一个出牌的人


@dataclass
class GameInfo:
    """游戏信息"""
    my_position: PlayerPosition = PlayerPosition.UNKNOWN
    is_landlord: bool = False
    is_farmer: bool = False
    bomb_count: int = 0
    current_multiplier: int = 1
    scores: Dict[str, int] = field(default_factory=dict)


class GameState:
    """
    游戏状态管理器

    使用状态机模式管理游戏流程，提供清晰的状态转换和查询接口
    """

    def __init__(self):
        """初始化游戏状态"""
        self.phase = GamePhase.IDLE
        self.card_state = CardState()
        self.game_info = GameInfo()
        self._phase_history: List[GamePhase] = []
        self._transition_callbacks: Dict[GamePhase, List[callable]] = {}

    # ==================== 状态查询 ====================

    def is_idle(self) -> bool:
        """是否处于空闲状态"""
        return self.phase == GamePhase.IDLE

    def is_waiting_start(self) -> bool:
        """是否等待游戏开始"""
        return self.phase == GamePhase.WAITING_START

    def is_bidding(self) -> bool:
        """是否在叫地主阶段"""
        return self.phase == GamePhase.BIDDING

    def is_doubling(self) -> bool:
        """是否在加倍阶段"""
        return self.phase == GamePhase.DOUBLING

    def is_playing(self) -> bool:
        """是否在出牌阶段"""
        return self.phase == GamePhase.CARD_PLAYING

    def is_game_over(self) -> bool:
        """是否游戏结束"""
        return self.phase == GamePhase.GAME_OVER

    def get_current_phase(self) -> GamePhase:
        """获取当前阶段"""
        return self.phase

    # ==================== 状态转换 ====================

    def transition_to(self, new_phase: GamePhase) -> bool:
        """
        转换到新阶段

        Args:
            new_phase: 新阶段

        Returns:
            是否转换成功
        """
        if not self._is_valid_transition(self.phase, new_phase):
            print(f"警告: 无效的状态转换 {self.phase} -> {new_phase}")
            return False

        old_phase = self.phase
        self.phase = new_phase
        self._phase_history.append(old_phase)

        # 执行转换回调
        self._execute_callbacks(new_phase)

        print(f"状态转换: {old_phase.name} -> {new_phase.name}")
        return True

    def _is_valid_transition(self, from_phase: GamePhase, to_phase: GamePhase) -> bool:
        """
        检查状态转换是否有效

        定义状态转换规则:
        IDLE -> WAITING_START
        WAITING_START -> BIDDING
        BIDDING -> DOUBLING
        DOUBLING -> CARD_PLAYING
        CARD_PLAYING -> GAME_OVER
        GAME_OVER -> IDLE (循环)
        任何阶段都可以回到 IDLE（重置）
        """
        valid_transitions = {
            GamePhase.IDLE: {GamePhase.WAITING_START},
            GamePhase.WAITING_START: {GamePhase.BIDDING, GamePhase.IDLE},
            GamePhase.BIDDING: {GamePhase.DOUBLING, GamePhase.IDLE},
            GamePhase.DOUBLING: {GamePhase.CARD_PLAYING, GamePhase.IDLE},
            GamePhase.CARD_PLAYING: {GamePhase.GAME_OVER, GamePhase.IDLE},
            GamePhase.GAME_OVER: {GamePhase.IDLE, GamePhase.WAITING_START},
        }

        return to_phase in valid_transitions.get(from_phase, set())

    def reset(self):
        """重置游戏状态"""
        self.phase = GamePhase.IDLE
        self.card_state = CardState()
        self.game_info = GameInfo()
        self._phase_history.clear()
        print("游戏状态已重置")

    # ==================== 回调管理 ====================

    def register_callback(self, phase: GamePhase, callback: callable):
        """
        注册阶段转换回调

        Args:
            phase: 触发回调的阶段
            callback: 回调函数
        """
        if phase not in self._transition_callbacks:
            self._transition_callbacks[phase] = []
        self._transition_callbacks[phase].append(callback)

    def _execute_callbacks(self, phase: GamePhase):
        """执行阶段转换回调"""
        if phase in self._transition_callbacks:
            for callback in self._transition_callbacks[phase]:
                try:
                    callback(self)
                except Exception as e:
                    print(f"回调执行失败: {e}")

    # ==================== 卡牌状态管理 ====================

    def update_my_cards(self, cards: List[str]):
        """更新我的手牌"""
        self.card_state.my_cards = sorted(cards, key=self._card_sort_key)

    def update_landlord_cards(self, cards: List[str]):
        """更新地主底牌"""
        self.card_state.landlord_cards = cards

    def update_played_cards(self, player: str, cards: List[str]):
        """
        更新已出的牌

        Args:
            player: 玩家标识
            cards: 出的牌
        """
        if player not in self.card_state.played_cards:
            self.card_state.played_cards[player] = []
        self.card_state.played_cards[player].extend(cards)

        self.card_state.last_played = cards
        self.card_state.last_player = player

    def remove_cards_from_hand(self, cards: List[str]):
        """从手牌中移除卡牌"""
        for card in cards:
            if card in self.card_state.my_cards:
                self.card_state.my_cards.remove(card)

    def get_my_cards(self) -> List[str]:
        """获取我的手牌"""
        return self.card_state.my_cards.copy()

    def get_remaining_card_count(self) -> int:
        """获取剩余手牌数量"""
        return len(self.card_state.my_cards)

    # ==================== 玩家位置管理 ====================

    def set_my_position(self, position: PlayerPosition):
        """设置我的位置"""
        self.game_info.my_position = position
        self.game_info.is_landlord = (position == PlayerPosition.LANDLORD)
        self.game_info.is_farmer = (position in [PlayerPosition.LANDLORD_UP, PlayerPosition.LANDLORD_DOWN])

    def get_my_position(self) -> PlayerPosition:
        """获取我的位置"""
        return self.game_info.my_position

    def is_my_turn(self, current_player: str) -> bool:
        """判断是否轮到我出牌"""
        # 这里需要根据实际游戏逻辑判断
        # 简化版本：当前玩家标识是否匹配我的位置
        return current_player == self.game_info.my_position.value

    # ==================== 游戏信息管理 ====================

    def increment_bomb_count(self):
        """炸弹计数 +1"""
        self.game_info.bomb_count += 1

    def set_multiplier(self, multiplier: int):
        """设置倍数"""
        self.game_info.current_multiplier = multiplier

    def update_score(self, player: str, score: int):
        """更新分数"""
        self.game_info.scores[player] = score

    def get_game_info(self) -> GameInfo:
        """获取游戏信息"""
        return self.game_info

    # ==================== 辅助方法 ====================

    @staticmethod
    def _card_sort_key(card: str) -> int:
        """卡牌排序键（从大到小）"""
        card_order = {
            'D': 16,  # 大王
            'X': 15,  # 小王
            '2': 14,
            'A': 13,
            'K': 12,
            'Q': 11,
            'J': 10,
            'T': 9,   # 10
            '9': 8,
            '8': 7,
            '7': 6,
            '6': 5,
            '5': 4,
            '4': 3,
            '3': 2,
        }
        return card_order.get(card, 0)

    def get_phase_history(self) -> List[GamePhase]:
        """获取阶段历史"""
        return self._phase_history.copy()

    def __repr__(self):
        return (
            f"GameState(phase={self.phase.name}, "
            f"position={self.game_info.my_position.name}, "
            f"cards={len(self.card_state.my_cards)})"
        )


# 使用示例
if __name__ == "__main__":
    # 创建游戏状态
    state = GameState()

    # 注册回调
    def on_bidding(state: GameState):
        print("进入叫地主阶段，准备决策...")

    state.register_callback(GamePhase.BIDDING, on_bidding)

    # 状态转换示例
    state.transition_to(GamePhase.WAITING_START)
    state.transition_to(GamePhase.BIDDING)
    state.update_my_cards(['D', 'X', '2', '2', 'A', 'K'])
    print(f"我的手牌: {state.get_my_cards()}")

    state.set_my_position(PlayerPosition.LANDLORD)
    print(f"我的位置: {state.get_my_position()}")

    state.transition_to(GamePhase.DOUBLING)
    state.transition_to(GamePhase.CARD_PLAYING)

    # 出牌
    state.update_played_cards("me", ['2', '2'])
    state.remove_cards_from_hand(['2', '2'])
    print(f"剩余手牌: {state.get_my_cards()}")

    print(f"\n游戏状态: {state}")

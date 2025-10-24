"""
简单使用示例 - 演示如何使用各个模块
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from master.utils import get_config
from master.core import GameState, GamePhase, PlayerPosition, RuleBasedAgent
from master.detection import CardDetector, TemplateDetector
from master.actions import MouseExecutor, CardSelector

# ============================================================
# 示例 1: 配置管理
# ============================================================
def example_config():
    """演示配置管理功能"""
    print("\n" + "="*50)
    print("示例 1: 配置管理")
    print("="*50)

    # 加载配置
    config = get_config()
    print(f"配置文件: {config.config_path}")

    # 获取配置值
    window_class = config.get('game.window_class')
    print(f"窗口类名: {window_class}")

    # 获取阈值
    bid_threshold = config.get_threshold('bidding.call_landlord')
    print(f"叫地主阈值: {bid_threshold}")

    # 设置分辨率并获取缩放后的区域
    config.set_resolution(1920, 1080)
    my_cards_region = config.get_region('my_hand_cards')
    print(f"手牌区域（1920x1080）: {my_cards_region}")

    # 恢复默认分辨率
    config.set_resolution(1440, 810)
    my_cards_region = config.get_region('my_hand_cards')
    print(f"手牌区域（1440x810）: {my_cards_region}")


# ============================================================
# 示例 2: 游戏状态管理
# ============================================================
def example_game_state():
    """演示游戏状态管理"""
    print("\n" + "="*50)
    print("示例 2: 游戏状态管理")
    print("="*50)

    # 创建状态管理器
    state = GameState()

    # 注册回调
    def on_bidding(state):
        print("  [回调] 进入叫地主阶段")

    def on_playing(state):
        print("  [回调] 进入出牌阶段")

    state.register_callback(GamePhase.BIDDING, on_bidding)
    state.register_callback(GamePhase.CARD_PLAYING, on_playing)

    # 状态转换
    print("\n状态转换:")
    state.transition_to(GamePhase.WAITING_START)
    state.transition_to(GamePhase.BIDDING)

    # 设置位置
    state.set_my_position(PlayerPosition.LANDLORD)
    print(f"我的位置: {state.get_my_position().name}")
    print(f"是地主: {state.game_info.is_landlord}")

    # 卡牌管理
    state.update_my_cards(['D', 'X', '2', '2', 'A', 'K', 'Q'])
    print(f"我的手牌: {state.get_my_cards()}")

    # 转换到出牌阶段
    state.transition_to(GamePhase.DOUBLING)
    state.transition_to(GamePhase.CARD_PLAYING)

    # 出牌
    state.update_played_cards("me", ['2', '2'])
    state.remove_cards_from_hand(['2', '2'])
    print(f"出牌后手牌: {state.get_my_cards()}")
    print(f"剩余手牌数: {state.get_remaining_card_count()}")


# ============================================================
# 示例 3: AI Agent 使用
# ============================================================
def example_agent():
    """演示 AI Agent 使用"""
    print("\n" + "="*50)
    print("示例 3: AI Agent 使用")
    print("="*50)

    config = get_config()

    # 创建规则based Agent（简单示例）
    agent = RuleBasedAgent(config, 'landlord')

    # 叫地主决策
    initial_cards = ['D', 'X', '2', 'A', 'K', 'Q']
    bid_result = agent.decide_bid(initial_cards)
    print(f"\n叫地主决策:")
    print(f"  手牌: {initial_cards}")
    print(f"  是否叫地主: {bid_result.should_bid}")
    print(f"  评分: {bid_result.score:.3f}")
    print(f"  置信度: {bid_result.confidence:.3f}")

    # 加倍决策
    my_cards = ['2', '2', 'A', 'K', 'Q', 'J', 'T', '9', '8', '7']
    double_result = agent.decide_double(my_cards, 'landlord')
    print(f"\n加倍决策:")
    print(f"  手牌: {my_cards}")
    print(f"  是否加倍: {double_result.should_double}")
    print(f"  加倍等级: {double_result.level}")
    print(f"  评分: {double_result.score:.3f}")

    # 出牌决策
    played_cards = []  # 可以任意出
    action_result = agent.decide_action(my_cards, played_cards, {})
    print(f"\n出牌决策:")
    print(f"  推荐出牌: {action_result.action}")
    print(f"  置信度: {action_result.confidence:.3f}")
    print(f"  理由: {action_result.reasoning}")


# ============================================================
# 示例 4: 检测器使用
# ============================================================
def example_detector():
    """演示检测器使用（需要实际图像）"""
    print("\n" + "="*50)
    print("示例 4: 检测器使用")
    print("="*50)

    config = get_config()

    # 创建卡牌检测器
    detector = CardDetector(config)
    print(f"卡牌检测器已创建")
    print(f"已加载 {len(detector.templates)} 个模板")

    # 创建 UI 检测器
    ui_detector = TemplateDetector(config)

    # 加载模板（示例）
    import os
    pics_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'pics'
    )

    chat_template = os.path.join(pics_dir, 'chat.png')
    if os.path.exists(chat_template):
        ui_detector.load_template('chat', chat_template)
        print(f"已加载 chat 模板")
    else:
        print(f"chat 模板不存在: {chat_template}")

    print("\n注意: 实际检测需要游戏截图，这里仅演示API")


# ============================================================
# 示例 5: 完整流程模拟
# ============================================================
def example_full_workflow():
    """演示完整的游戏流程（模拟）"""
    print("\n" + "="*50)
    print("示例 5: 完整流程模拟")
    print("="*50)

    # 初始化
    config = get_config()
    state = GameState()
    agent = RuleBasedAgent(config, 'landlord')

    print("\n1. 游戏开始，等待叫地主...")
    state.transition_to(GamePhase.WAITING_START)
    state.transition_to(GamePhase.BIDDING)

    # 叫地主阶段
    initial_cards = ['D', 'X', '2', 'A', 'K', 'Q']
    bid_result = agent.decide_bid(initial_cards)
    print(f"   初始手牌: {initial_cards}")
    print(f"   AI 决策: {'叫地主' if bid_result.should_bid else '不叫'}")

    # 假设叫到了地主
    print("\n2. 成为地主，获得底牌...")
    state.set_my_position(PlayerPosition.LANDLORD)
    landlord_cards = ['2', 'A', 'K']
    all_cards = initial_cards + landlord_cards
    state.update_my_cards(all_cards)
    state.update_landlord_cards(landlord_cards)
    print(f"   底牌: {landlord_cards}")
    print(f"   总手牌: {state.get_my_cards()}")

    # 加倍阶段
    print("\n3. 加倍阶段...")
    state.transition_to(GamePhase.DOUBLING)
    double_result = agent.decide_double(all_cards, 'landlord')
    print(f"   AI 决策: {'加倍' if double_result.should_double else '不加倍'}")

    # 出牌阶段
    print("\n4. 开始出牌...")
    state.transition_to(GamePhase.CARD_PLAYING)

    # 模拟几轮出牌
    for round_num in range(1, 4):
        print(f"\n   第 {round_num} 轮:")
        my_cards = state.get_my_cards()
        action_result = agent.decide_action(my_cards, [], {})

        print(f"   当前手牌: {my_cards}")
        print(f"   AI 推荐: {action_result.action}")

        # 模拟出牌
        if action_result.action:
            state.update_played_cards("me", action_result.action)
            state.remove_cards_from_hand(action_result.action)
            print(f"   剩余手牌: {state.get_my_cards()} ({state.get_remaining_card_count()} 张)")

    print("\n5. 游戏结束")
    state.transition_to(GamePhase.GAME_OVER)


# ============================================================
# 主函数
# ============================================================
def main():
    """运行所有示例"""
    print("\n" + "#"*50)
    print("# DouZero Agent - 使用示例")
    print("#"*50)

    try:
        example_config()
        example_game_state()
        example_agent()
        example_detector()
        example_full_workflow()

        print("\n" + "="*50)
        print("所有示例运行完成！")
        print("="*50)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

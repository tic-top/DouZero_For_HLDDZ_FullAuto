# 架构设计文档

## 概述

本文档详细说明 DouZero Agent 的架构设计、模块职责和设计决策。

## 设计原则

### 1. 关注点分离 (Separation of Concerns)

每个模块专注于单一职责：

- **检测模块** - 只负责图像识别和检测
- **决策模块** - 只负责 AI 决策逻辑
- **执行模块** - 只负责动作执行
- **状态模块** - 只负责状态管理

### 2. 开闭原则 (Open/Closed Principle)

- 对扩展开放：可以轻松添加新的 Agent、检测器、执行器
- 对修改封闭：添加新功能不需要修改现有代码

### 3. 依赖倒置 (Dependency Inversion)

- 依赖抽象而非具体实现
- 所有模块都定义了抽象基类

### 4. 单一职责 (Single Responsibility)

- 每个类只有一个改变的理由
- 避免"上帝类"

## 模块架构

```
┌─────────────────────────────────────────────────┐
│              Main Controller                     │
│          (DouZeroGameAgent)                      │
└────────────┬──────────────┬─────────────────────┘
             │              │
      ┌──────┴───┐    ┌────┴─────┐
      │  Config  │    │  State   │
      │  Loader  │    │ Manager  │
      └──────────┘    └──────────┘
             │              │
    ┌────────┴────────┬─────┴──────┬────────────┐
    │                 │            │            │
┌───┴────┐      ┌────┴────┐  ┌───┴────┐  ┌────┴────┐
│Detector│      │ Agent   │  │Executor│  │ Utils   │
│ Module │      │ Module  │  │ Module │  │ Module  │
└────────┘      └─────────┘  └────────┘  └─────────┘
```

## 核心模块详解

### 1. 配置管理 (utils/config_loader.py)

**职责：**
- 加载和解析 YAML 配置文件
- 提供嵌套键访问接口
- 自动分辨率缩放

**设计决策：**
- 使用 YAML 而非 JSON：更易读、支持注释
- 单例模式：确保全局配置一致性
- 懒加载：只在需要时加载配置

**接口：**
```python
class ConfigLoader:
    def get(key_path: str, default=None) -> Any
    def get_region(region_name: str) -> Tuple[int, int, int, int]
    def get_threshold(threshold_path: str) -> float
    def set_resolution(width: int, height: int)
```

### 2. 游戏状态管理 (core/game_state.py)

**职责：**
- 管理游戏阶段转换
- 跟踪卡牌状态
- 管理玩家信息

**设计模式：**
- 状态机模式
- 观察者模式（回调机制）

**状态转换图：**
```
IDLE → WAITING_START → BIDDING → DOUBLING → CARD_PLAYING → GAME_OVER
  ↑                                                              ↓
  └──────────────────────────────────────────────────────────────┘
```

**接口：**
```python
class GameState:
    # 状态查询
    def is_bidding() -> bool
    def is_playing() -> bool

    # 状态转换
    def transition_to(new_phase: GamePhase) -> bool

    # 卡牌管理
    def update_my_cards(cards: List[str])
    def remove_cards_from_hand(cards: List[str])

    # 回调
    def register_callback(phase: GamePhase, callback: callable)
```

### 3. 检测器 (detection/detector.py)

**职责：**
- 图像识别
- 模板匹配
- 卡牌检测

**设计模式：**
- 策略模式（不同的检测策略）
- 模板方法模式

**类层次：**
```
Detector (抽象基类)
    ├── TemplateDetector (模板匹配)
    └── CardDetector (卡牌检测)
```

**接口：**
```python
class Detector(ABC):
    @abstractmethod
    def detect(image: Image, **kwargs) -> Optional[Any]

class CardDetector(TemplateDetector):
    def detect_cards(image: Image, card_type: str, region: Tuple) -> List[str]
```

### 4. AI Agent (core/agent.py & agents/)

**职责：**
- AI 决策逻辑
- 叫地主/加倍判断
- 出牌推荐

**设计模式：**
- 策略模式（不同的 Agent 策略）
- 工厂模式（创建不同类型的 Agent）

**类层次：**
```
Agent (抽象基类)
    ├── RuleBasedAgent (规则based)
    ├── DouZeroAgent (深度学习)
    └── HybridAgent (混合策略)
```

**接口：**
```python
class Agent(ABC):
    @abstractmethod
    def decide_action(my_cards, played_cards, game_state) -> DecisionResult

    @abstractmethod
    def decide_bid(initial_cards) -> BidDecision

    @abstractmethod
    def decide_double(my_cards, position, landlord_cards) -> DoubleDecision
```

### 5. 动作执行器 (actions/executor.py)

**职责：**
- 鼠标操作
- 卡牌选择
- 按钮点击

**设计模式：**
- 命令模式（封装操作为对象）
- 责任链模式（验证-执行链）

**类层次：**
```
ActionExecutor (抽象基类)
    ├── MouseExecutor (鼠标操作)
    ├── CardSelector (卡牌选择)
    └── BidExecutor (叫地主/加倍)
```

**接口：**
```python
class ActionExecutor(ABC):
    @abstractmethod
    def execute(**kwargs)

class CardSelector(ActionExecutor):
    def select_cards(my_cards, cards_to_play, hand_region) -> bool
    def click_play_button(button_region)
```

## 数据流

### 1. 叫地主阶段

```
Screenshot → CardDetector.detect_cards()
                    ↓
           initial_cards: List[str]
                    ↓
           Agent.decide_bid(initial_cards)
                    ↓
           BidDecision(should_bid, score, confidence)
                    ↓
           BidExecutor.call_landlord() or pass_landlord()
                    ↓
           GameState.transition_to(DOUBLING)
```

### 2. 出牌阶段

```
Screenshot → CardDetector.detect_cards()
                    ↓
           my_cards: List[str]
                    ↓
           Agent.decide_action(my_cards, played_cards, game_state)
                    ↓
           DecisionResult(action, confidence, alternatives)
                    ↓
           CardSelector.select_cards(my_cards, action, hand_region)
                    ↓
           CardSelector.click_play_button()
                    ↓
           GameState.update_played_cards()
           GameState.remove_cards_from_hand()
```

## 可扩展性

### 添加新的检测器

```python
from master.detection import Detector

class OCRDetector(Detector):
    """使用 OCR 识别卡牌"""
    def detect(self, image, **kwargs):
        # 使用 pytesseract 或其他 OCR 工具
        return ocr_result
```

### 添加新的 Agent

```python
from master.core import Agent

class ReinforcementAgent(Agent):
    """基于强化学习的 Agent"""
    def decide_action(self, my_cards, played_cards, game_state):
        # 使用 RL 模型决策
        return DecisionResult(...)
```

### 添加新的执行器

```python
from master.actions import ActionExecutor

class KeyboardExecutor(ActionExecutor):
    """使用键盘操作（适配其他游戏）"""
    def execute(self, **kwargs):
        # 使用 pyautogui 或 pynput
        pass
```

## 错误处理

### 1. 配置错误

- 配置文件不存在 → 抛出 FileNotFoundError
- 配置格式错误 → 抛出 ValueError
- 缺少必需配置 → 使用默认值 + 警告

### 2. 检测失败

- 模板匹配失败 → 返回 None
- 卡牌识别错误 → 重试机制（可配置）
- 超时 → 降低置信度阈值

### 3. 决策失败

- 模型加载失败 → 降级到规则 Agent
- 决策异常 → 返回保守策略（过牌）

### 4. 执行失败

- 窗口句柄丢失 → 重新查找窗口
- 点击失败 → 重试 + 记录日志

## 性能优化

### 1. 模板缓存

所有模板图像在初始化时加载一次，缓存在内存中。

### 2. 配置缓存

配置文件解析后缓存，避免重复解析。

### 3. 坐标预计算

分辨率缩放系数预计算，避免每次计算。

### 4. 并发优化（未来）

- 图像检测可以并行处理
- 多个 Agent 可以同时决策（投票机制）

## 测试策略

### 1. 单元测试

每个模块都应有独立的单元测试：

```python
# test_config_loader.py
def test_get_config():
    config = get_config()
    assert config.get('game.window_class') == 'UnityWndClass'

# test_game_state.py
def test_state_transition():
    state = GameState()
    assert state.transition_to(GamePhase.BIDDING)
    assert state.is_bidding()
```

### 2. 集成测试

测试模块间协作：

```python
def test_detection_and_decision():
    detector = CardDetector(config)
    agent = DouZeroAgent(config, 'landlord')

    cards = detector.detect_cards(test_image, 'my')
    decision = agent.decide_bid(cards)

    assert decision.should_bid in [True, False]
```

### 3. 端到端测试

模拟完整游戏流程（需要 mock）。

## 未来改进

### 短期

1. 完善游戏循环逻辑
2. 添加日志系统
3. 添加性能监控
4. 编写单元测试

### 中期

1. 支持更多分辨率
2. 添加 OCR 检测器
3. 实现混合 Agent
4. 添加 GUI 界面

### 长期

1. 支持其他斗地主游戏
2. 多进程/多线程优化
3. Web 服务接口
4. 机器学习模型训练工具

## 总结

这个架构设计遵循了良好的软件工程原则：

- ✅ 模块化：每个模块职责清晰
- ✅ 可扩展：易于添加新功能
- ✅ 可测试：接口清晰，易于测试
- ✅ 可维护：代码组织良好，易于理解
- ✅ 灵活性：支持多种配置和策略

相比原版的单文件实现，新架构更适合长期维护和团队协作。

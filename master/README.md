# DouZero Agent - 模块化斗地主 AI 框架

> 一个重构的、更加灵活和可扩展的斗地主 AI Agent 框架

---

## ⚠️ 重要提示

**此目录的代码还未完成，不能用于自动打牌！**

如果你想运行**自动打牌程序**，请使用**根目录的 `main.py`**：

```bash
# 回到根目录
cd ..

# 运行完整的自动打牌程序
python main.py
```

**master/ 目录的作用：**
- ✅ 学习 Python 项目架构
- ✅ 使用调试工具（截图、检测、诊断）
- ✅ 作为代码重构的参考
- ❌ **不能自动打牌**（游戏逻辑未实现）

详细说明请查看：[根目录的 HOW_TO_RUN.md](../HOW_TO_RUN.md)

---

## 📋 简介

这是基于原有 DouZero 项目重构的新版本，采用模块化设计，提供了清晰的抽象接口和灵活的配置系统。

### ✨ 主要改进

1. **模块化架构** - 清晰分离关注点（检测、决策、执行）
2. **灵活配置** - YAML 配置文件，支持多分辨率自动缩放
3. **可扩展性** - 抽象接口设计，易于添加新功能
4. **状态管理** - 清晰的状态机模式，游戏流程更易理解
5. **统一决策接口** - 支持多种 AI Agent（DouZero、规则based、混合）

## 🏗️ 架构设计

```
master/
├── config/              # 配置文件
│   └── default.yaml     # 默认配置
├── core/                # 核心模块
│   ├── agent.py         # AI Agent 抽象基类
│   └── game_state.py    # 游戏状态管理器
├── detection/           # 检测模块
│   └── detector.py      # 检测器（模板匹配、卡牌识别）
├── actions/             # 动作执行模块
│   └── executor.py      # 执行器（鼠标、卡牌选择）
├── agents/              # AI Agent 实现
│   └── douzero_agent.py # DouZero AI Agent
├── utils/               # 工具模块
│   └── config_loader.py # 配置加载器
└── main.py              # 主入口
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 确保已安装原项目的依赖
pip install -r ../requirements.txt

# 额外需要 PyYAML
pip install pyyaml
```

### 2. 配置文件

编辑 `config/default.yaml`，根据你的游戏窗口调整参数：

```yaml
# 游戏窗口配置
game:
  window_class: "UnityWndClass"
  window_title: "欢乐斗地主"
  target_resolution:
    width: 1440
    height: 810

# AI 决策阈值
thresholds:
  bidding:
    call_landlord: 0.2
  doubling:
    landlord_stole_1: 0.5
```

### 3. 运行

```bash
# 运行 Agent（默认地主位置）
python main.py

# 指定位置
python main.py --position landlord_up

# 使用自定义配置
python main.py --config my_config.yaml
```

## 📚 核心模块说明

### 1. 配置管理 (`utils/config_loader.py`)

```python
from master.utils import get_config

# 加载配置
config = get_config('config/default.yaml')

# 获取配置值
window_class = config.get('game.window_class')
threshold = config.get_threshold('bidding.call_landlord')

# 自动缩放坐标
config.set_resolution(1920, 1080)
region = config.get_region('my_hand_cards')  # 自动缩放到新分辨率
```

**特点：**
- 支持嵌套键访问（`game.window_class`）
- 自动分辨率缩放（基准 1440x810）
- 动态更新和保存配置

### 2. 游戏状态管理 (`core/game_state.py`)

```python
from master.core import GameState, GamePhase, PlayerPosition

# 创建状态管理器
state = GameState()

# 状态转换
state.transition_to(GamePhase.BIDDING)
state.transition_to(GamePhase.CARD_PLAYING)

# 卡牌管理
state.update_my_cards(['D', 'X', '2', '2', 'A'])
state.remove_cards_from_hand(['2', '2'])

# 位置设置
state.set_my_position(PlayerPosition.LANDLORD)
```

**特点：**
- 清晰的状态机（IDLE → WAITING → BIDDING → DOUBLING → PLAYING → OVER）
- 状态转换验证
- 回调机制（在特定阶段触发）

### 3. 检测器 (`detection/detector.py`)

```python
from master.detection import CardDetector, TemplateDetector

# 卡牌检测
card_detector = CardDetector(config)
my_cards = card_detector.detect_cards(screenshot, card_type='my')
# 返回: ['D', 'X', '2', '2', 'A', 'K']

# UI 元素检测
ui_detector = TemplateDetector(config)
ui_detector.load_template('chat', 'pics/chat.png')
position = ui_detector.detect(screenshot, 'chat', region=(1302, 744, 117, 56))
```

**特点：**
- 抽象基类 `Detector`
- 模板匹配检测器 `TemplateDetector`
- 专门的卡牌检测器 `CardDetector`
- 自动去重和过滤

### 4. AI Agent (`core/agent.py` & `agents/douzero_agent.py`)

```python
from master.agents import DouZeroAgent

# 创建 DouZero Agent
agent = DouZeroAgent(config, 'landlord')

# 叫地主决策
bid_result = agent.decide_bid(['D', 'X', '2', 'A', 'K', 'Q'])
# BidDecision(should_bid=True, score=0.85, confidence=0.65)

# 加倍决策
double_result = agent.decide_double(my_cards, 'landlord')
# DoubleDecision(should_double=True, level=2, score=1.2, confidence=0.7)

# 出牌决策
action_result = agent.decide_action(my_cards, played_cards, game_state)
# DecisionResult(action=['2', '2'], confidence=0.92, alternatives=[...])
```

**特点：**
- 统一的 Agent 接口
- 封装 DouZero 深度学习模型
- 返回结构化的决策结果
- 支持备选方案

### 5. 动作执行器 (`actions/executor.py`)

```python
from master.actions import MouseExecutor, CardSelector, BidExecutor

# 鼠标操作
mouse = MouseExecutor(config, window_handle)
mouse.click(100, 200, relative=True)

# 卡牌选择
card_selector = CardSelector(config, mouse)
card_selector.select_cards(
    my_cards=['D', 'X', '2', '2', 'A'],
    cards_to_play=['2', '2'],
    hand_region=(180, 560, 1050, 90)
)
card_selector.click_play_button(button_region)

# 叫地主操作
bid_executor = BidExecutor(config, mouse)
bid_executor.call_landlord()
bid_executor.double(level=2)
```

**特点：**
- 抽象的动作执行器基类
- 分离鼠标操作和游戏逻辑
- 智能卡牌选择（处理重复卡牌）
- 可选的操作验证

## 🔧 配置说明

### 分辨率适配

框架支持自动分辨率缩放。所有坐标基于 1440x810 分辨率定义，运行时会自动缩放到实际窗口大小。

```yaml
regions:
  base_resolution: [1440, 810]
  my_hand_cards: [180, 560, 1050, 90]  # 会自动缩放
```

### 阈值调整

所有 AI 决策阈值都可以在配置文件中调整：

```yaml
thresholds:
  bidding:
    call_landlord: 0.2      # 叫地主阈值
    steal_landlord_1: 0.4   # 抢地主阈值
  doubling:
    landlord_stole_1: 0.5   # 地主加倍阈值
    farmer_high: 1.3        # 农民加倍阈值
```

### 模型路径

支持多种 DouZero 模型：

```yaml
models:
  douzero:
    type: "resnet"  # resnet, general, default
    landlord: "baselines/resnet/resnet_landlord.ckpt"
    landlord_up: "baselines/resnet/resnet_landlord_up.ckpt"
    landlord_down: "baselines/resnet/resnet_landlord_down.ckpt"
```

## 🎯 使用示例

### 示例1：自定义 AI Agent

```python
from master.core import Agent, DecisionResult

class MyCustomAgent(Agent):
    def decide_action(self, my_cards, played_cards, game_state):
        # 自定义决策逻辑
        return DecisionResult(
            action=['3'],
            confidence=0.8,
            reasoning="出最小的牌"
        )

    def decide_bid(self, initial_cards):
        # 自定义叫地主逻辑
        return BidDecision(should_bid=True, score=0.5, confidence=0.5)

    def decide_double(self, my_cards, position, landlord_cards=None):
        # 自定义加倍逻辑
        return DoubleDecision(should_double=False, level=1, score=0.3, confidence=0.3)
```

### 示例2：组合使用

```python
from master.utils import get_config
from master.core import GameState, GamePhase
from master.agents import DouZeroAgent
from master.detection import CardDetector

# 初始化
config = get_config()
state = GameState()
agent = DouZeroAgent(config, 'landlord')
detector = CardDetector(config)

# 检测卡牌
my_cards = detector.detect_cards(screenshot, card_type='my')
state.update_my_cards(my_cards)

# AI 决策
decision = agent.decide_action(my_cards, [], {'infoset': infoset})
print(f"推荐出牌: {decision.action}, 置信度: {decision.confidence}")

# 执行动作
card_selector.select_cards(my_cards, decision.action, hand_region)
```

## 📝 对比原版的改进

| 方面 | 原版 | 新版 (master/) |
|------|------|----------------|
| **代码组织** | 1400+ 行单文件 | 模块化，每个模块 < 400 行 |
| **配置** | 硬编码 + JSON | YAML 配置，支持分辨率缩放 |
| **扩展性** | 紧耦合 | 抽象接口，易扩展 |
| **状态管理** | 混乱的标志位 | 清晰的状态机 |
| **AI 接口** | 直接调用模型 | 统一的 Agent 接口 |
| **可测试性** | 困难 | 每个模块可独立测试 |

## 🛠️ 开发指南

### 添加新的检测器

```python
from master.detection import Detector

class MyDetector(Detector):
    def detect(self, image, **kwargs):
        # 实现检测逻辑
        return detection_result
```

### 添加新的 Agent

```python
from master.core import Agent

class MyAgent(Agent):
    def decide_action(self, my_cards, played_cards, game_state):
        # 实现决策逻辑
        pass
```

### 注册状态回调

```python
def on_bidding_phase(state):
    print("进入叫地主阶段")

state.register_callback(GamePhase.BIDDING, on_bidding_phase)
```

## ⚠️ 注意事项

1. **窗口要求**：游戏窗口需要可见（不能最小化）
2. **分辨率**：推荐使用 1440x810，其他分辨率会自动缩放
3. **模型文件**：需要确保 DouZero 模型文件存在
4. **依赖**：需要安装原项目的所有依赖

## 📄 许可证

继承原项目的 Apache 2.0 许可证。

## 🙏 致谢

- 基于 [DouZero](https://github.com/kwai/DouZero) 深度学习框架
- 原项目作者的优秀工作

---

**注意**：这是一个重构的框架版本，主要用于演示模块化设计和架构改进。完整的游戏循环逻辑需要进一步实现。

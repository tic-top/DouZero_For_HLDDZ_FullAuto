# 📚 欢乐斗地主自动化项目架构分析

## 🏗️ 整体架构

这是一个基于 **图像识别 + AI 决策** 的斗地主自动游戏系统。

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层 (UI)                        │
│                      MyPyQT_Form (PyQt5)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                      控制逻辑层 (Worker)                      │
│              QThread - 游戏自动化主循环                        │
└──────────────┬────────────────┬─────────────────────────────┘
               │                │
       ┌───────▼────────┐  ┌────▼─────────┐
       │  图像识别层     │  │  AI 决策层    │
       │  GameHelper    │  │  Models      │
       └───────┬────────┘  └────┬─────────┘
               │                │
       ┌───────▼────────────────▼─────────┐
       │         游戏交互层                │
       │   (截图、鼠标点击、模板匹配)       │
       └──────────────────────────────────┘
```

## 📁 核心文件结构

### 1. **主程序入口**

#### `mian.py` (注意是 mian 不是 main)
- **作用**: 整个程序的入口点
- **核心类**:
  - `Worker(QThread)`: 游戏自动化的工作线程
  - `MyPyQT_Form`: PyQt5 图形界面

**工作流程**:
```
启动 → 初始化UI → 用户点击"自动"/"手动" → 启动Worker线程 → 游戏循环
```

### 2. **图像识别层**

#### `GameHelper.py`
- **作用**: 封装所有图像识别和鼠标操作
- **核心功能**:
  ```python
  class GameHelper:
      def __init__(self):
          self.Pics = {}      # 存储所有模板图片 (PIL格式)
          self.PicsCV = {}    # 存储所有模板图片 (OpenCV格式)
          # 从 ./pics/ 目录加载所有 .png 图片

      def Screenshot(self, region=None):
          # 截取游戏窗口 (固定1440x810)

      def LocateOnScreen(self, templateName, region, confidence=0.8):
          # 在截图中查找模板图片
          # 使用 OpenCV 模板匹配 (cv2.matchTemplate)

      def ClickOnImage(self, templateName, region):
          # 查找并点击图片位置
  ```

**依赖**:
- **窗口大小**: 必须是 **1440 x 810**
- **模板图片**: 存储在 `./pics/` 目录
  - `m*.png` - 手牌模板 (m3.png, m4.png, ...)
  - `o*.png` - 其他玩家出牌模板
  - `c*.png` - 中央出牌区模板
  - `z*.png` - 底牌模板
  - 按钮模板: `start_game.png`, `continue.png`, etc.

### 3. **AI 决策层**

#### `BidModel.py` - 叫牌模型
```python
class Net2(nn.Module):
    # 神经网络模型
    # 输入: 手牌的 one-hot 编码 (1x60)
    # 输出: 叫牌得分 (0-1)

def predict_score(cards_str):
    # 输入: "3456789TJQKA2XD" (17或20张牌)
    # 输出: 叫牌得分
    # 用途: 决定是否叫地主/抢地主
```

#### `LandlordModel.py` - 地主出牌模型
```python
class Net(nn.Module):
    # 地主决策网络
    # 输入: 手牌 one-hot
    # 输出: 出牌得分

def predict_by_model(cards_str, three_cards):
    # 预测地主拿到三张底牌后的胜率
    # 用于决定是否加倍

def init_model(model_path):
    # 加载预训练模型
    # 默认: baselines/resnet/resnet_landlord.ckpt
```

#### `FarmerModel.py` - 农民出牌模型
```python
def predict(cards_str, position):
    # 预测农民的胜率
    # position: "farmer", "up", "down"
```

#### `douzero/` 目录 - DouZero 核心
```
douzero/
├── env/
│   ├── game.py         # 游戏环境模拟
│   └── move_detector.py # 牌型检测
├── evaluation/
│   └── deep_agent.py   # AI 决策代理
└── dmc/
    └── models.py       # ResNet 模型定义
```

**核心类**:
```python
class GameEnv:
    """斗地主游戏环境"""
    def step(self, position, action):
        # 执行一个动作
        # 返回: (action_message, action_list)
        # action_message: {'action': '34567', 'win_rate': 0.95}
        # action_list: [(牌型1, 得分1), (牌型2, 得分2), ...]

class DeepAgent:
    """深度学习决策代理"""
    def __init__(self, position, model_path):
        # position: 'landlord', 'landlord_up', 'landlord_down'
        # 加载对应的 ResNet 模型
```

### 4. **辅助模块**

#### `DetermineColor.py`
- 颜色分类器,用于区分大小王

#### `MainWindow.py`
- PyQt5 UI 界面定义 (由 Qt Designer 生成)

## 🔄 完整游戏流程

### 阶段 1: 初始化
```python
Worker.__init__():
    1. 加载模型路径配置
    2. 初始化 GameHelper
    3. 从 pics/ 加载所有模板图片
    4. 初始化地主模型 (LandlordModel.init_model)
```

### 阶段 2: 等待游戏开始
```python
Worker.detect_start_btn():
    循环检测:
    - "快速开始" 按钮 → 点击
    - "继续" 按钮 → 点击
    - "胜利/失败" 标志 → 重置环境

Worker.before_start():
    1. 等待进入游戏大厅 (检测"聊天"按钮)
    2. 等待游戏开始 (检测底牌区域)
```

### 阶段 3: 叫牌/抢地主/加倍
```python
Worker.choose_multiples_stage():
    循环:
    1. 识别手牌 (find_my_cards)
       - 在区域 (180, 560, 1050, 90) 截图
       - 对每张牌用模板匹配识别
       - 返回: "3456789TJQKA2" 格式

    2. 如果检测到 "叫地主" 按钮:
       - 使用 BidModel.predict_score(cards) 计算得分
       - 如果得分 > threshold[0]: 点击"叫地主"
       - 否则: 点击"不叫"

    3. 如果检测到 "抢地主" 按钮:
       - 根据 threshold[1] 或 threshold[2] 决定

    4. 如果检测到 "加倍" 按钮:
       a. 识别三张底牌
       b. 使用 LandlordModel/FarmerModel 预测胜率
       c. 根据胜率决定是否加倍/超级加倍
```

### 阶段 4: 出牌阶段
```python
Worker.init_cards():
    1. 识别底牌 (3张)
    2. 识别玩家角色:
       - 检测地主标志在哪个位置
       - 确定自己是 地主/地主上家/地主下家
    3. 识别手牌 (17或20张)
    4. 初始化游戏环境:
       env = GameEnv(AI)
       env.card_play_init(card_play_data_list)

Worker.game_start():
    循环直到游戏结束:

    当轮到玩家出牌 (play_order == 0):
        1. 调用 env.step(position, update=False)
           - 获取 AI 推荐的出牌

        2. 自动模式:
           - 如果 action == "": 点击"要不起"/"不出"
           - 否则: 选牌 → 点击"出牌"

        3. 手动模式:
           - 显示 AI 推荐
           - 等待玩家手动出牌
           - 识别玩家出的牌

        4. 更新环境: env.step(position, played_cards)

    当轮到下家出牌 (play_order == 1):
        1. 等待检测到下家出牌
        2. 识别出的牌
        3. 更新环境

    当轮到上家出牌 (play_order == 2):
        同上
```

## 🎯 关键算法

### 1. 扑克牌识别
```python
def find_cards(img, pos, mark="m", confidence=0.8):
    """
    mark: "m" (手牌), "o" (其他玩家), "c" (中央), "z" (底牌)

    流程:
    1. 遍历 AllCards = ['D', 'X', '2', 'A', ..., '3']
    2. 对每张牌用模板匹配: cv2.matchTemplate
    3. 对大小王特殊处理: 颜色分类器区分红/黑
    4. 滤波去重: cards_filter (同一张牌可能多次匹配)
    5. 返回: "3456789TJQKA2XD"
    """
```

### 2. 选牌算法
```python
def click_cards(out_cards):
    """
    out_cards: "334455" - 要出的牌

    流程:
    1. 识别当前手牌位置
    2. 找到"up_left"标记 → 计算每张牌的坐标
    3. 从右向左逐个点击要出的牌
    4. 检测是否有误点 → 纠正
    5. 点击"出牌"按钮
    """
```

### 3. AI 决策
```python
DeepAgent.step():
    """
    输入: 当前游戏状态
    输出: (最佳动作, 前N个候选动作列表)

    ResNet 模型:
    - 输入: 状态向量 (手牌、历史出牌、剩余牌数...)
    - 输出: Q值 (每个合法动作的评分)
    - 选择: Q值最高的动作
    """
```

## 📊 数据流

```
用户点击"自动"
    ↓
Worker.run()
    ↓
循环: detect_start_btn()
    ↓
进入游戏: before_start()
    ↓
叫牌阶段: choose_multiples_stage()
    ├→ find_my_cards() → BidModel.predict() → 点击"叫地主"
    └→ find_three_cards() → LandlordModel.predict() → 点击"加倍"
    ↓
出牌阶段: game_start()
    ├→ find_my_cards()
    ├→ env.step() → DeepAgent → AI 推荐
    ├→ click_cards() → 执行出牌
    └→ find_other_cards() → 识别对手出牌
    ↓
游戏结束 → 重新开始
```

## ⚙️ 配置参数

### 窗口大小要求
- **固定**: 1440 x 810
- **原因**: 所有坐标和区域都是硬编码的

### 关键区域坐标 (Worker类)
```python
MyHandCardsPos = (180, 560, 1050, 90)    # 我的手牌
LPlayedCardsPos = (320, 280, 400, 120)   # 左边出牌
RPlayedCardsPos = (720, 280, 400, 120)   # 右边出牌
MPlayedCardsPos = (300, 350, 800, 100)   # 我的出牌
LandlordCardsPos = (600, 33, 220, 103)   # 底牌
PassBtnPos = (200, 450, 1000, 120)       # 要不起按钮
```

### AI 阈值 (data.json)
```json
{
  "bid1": 0.2,    // 叫地主阈值
  "bid2": 0.4,    // 抢地主阈值1
  "bid3": 0.5,    // 抢地主阈值2
  "jiabei1": 0.5, // 加倍阈值 (抢到)
  "jiabei2": 0.4,
  "jiabei3": 0.6, // 加倍阈值 (没抢到)
  "jiabei4": 0.5,
  "jiabei5": 1.3, // 农民加倍阈值
  "jiabei6": 1.1,
  "mingpai": 1.5  // 明牌阈值
}
```

## 🔧 技术栈

- **UI**: PyQt5
- **图像识别**: OpenCV (模板匹配)
- **AI 模型**: PyTorch (ResNet)
- **游戏交互**: pywin32 (截图、鼠标控制)
- **图像处理**: Pillow, numpy, scikit-image

## 💡 系统优缺点

### ✅ 优点
1. **AI 决策强大**: 基于 DouZero 训练的 ResNet 模型
2. **自动化完整**: 从开始到结束全自动
3. **GUI 友好**: PyQt5 界面,参数可调

### ❌ 缺点
1. **窗口大小固定**: 必须 1440x810
2. **模板依赖**: 游戏界面更新需要重新截取模板
3. **识别速度**: 每次识别约 0.1-0.2 秒
4. **鲁棒性**: 对光照、分辨率敏感

## 🆕 新 OCR 系统对比

| 特性 | 旧系统 (模板匹配) | 新系统 (OCR) |
|------|-----------------|-------------|
| 窗口要求 | 固定 1440x810 | 任意大小 |
| 按钮识别 | 模板图片 | 文字识别 |
| 维护成本 | 高 | 低 |
| 识别速度 | 快 (~0.1s) | 中等 (~0.5s) |
| 抗更新性 | 差 | 好 |

---

希望这个分析对你有帮助!如果有任何问题,请随时问我。

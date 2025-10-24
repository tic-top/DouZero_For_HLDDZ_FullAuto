# 如何运行自动打牌程序

## 🎯 重要说明

**项目中有两个 main.py：**

1. **`main.py`**（根目录）- ✅ **这是真正的自动打牌程序**
   - 文件大小：69KB
   - 完整功能：自动检测卡牌、自动出牌、叫地主等
   - 使用 PyQt5 GUI 界面

2. **`master/main.py`**（master 目录）- ❌ **这只是一个新的框架/演示**
   - 文件大小：较小
   - 状态：未完成，只有基础框架
   - 功能：只能找窗口、检测 Chat 图标，**不能自动打牌**

## 🚀 如何运行自动打牌

### 方法 1：使用根目录的 main.py（推荐）

```bash
# 回到项目根目录
cd C:\Users\29058\Desktop\DouZero_For_HLDDZ_FullAuto

# 运行完整的自动打牌程序
python main.py
```

**这会启动：**
- ✅ PyQt5 图形界面
- ✅ 自动检测游戏窗口
- ✅ 自动识别卡牌
- ✅ AI 决策出牌
- ✅ 自动叫地主/抢地主
- ✅ 自动加倍
- ✅ 完整的游戏循环

### 方法 2：使用 GUI 主窗口

如果有 `MainWindow.py`（PyQt5 界面）：

```bash
python MainWindow.py
```

## 📁 项目结构说明

```
DouZero_For_HLDDZ_FullAuto/
│
├── main.py                    ← ✅ 真正的自动打牌程序（使用这个！）
├── GameHelper.py              ← 游戏辅助类（截图、点击等）
├── MainWindow.py              ← PyQt5 主窗口
├── BidModel.py                ← 叫地主 AI 模型
├── LandlordModel.py           ← 地主 AI 模型
├── FarmerModel.py             ← 农民 AI 模型
├── DetermineColor.py          ← 卡牌颜色识别
│
├── master/                    ← ❌ 新框架（未完成，不要用这个）
│   ├── main.py                ← 只是演示框架，不能自动打牌
│   ├── core/                  ← 核心模块（重构中）
│   ├── detection/             ← 检测模块（重构中）
│   ├── actions/               ← 动作执行（重构中）
│   └── config/                ← 配置文件
│
├── pics/                      ← 模板图片（chat.png, 卡牌模板等）
├── douzero/                   ← DouZero AI 算法
└── baselines/                 ← 预训练模型
```

## 🎮 完整使用流程

### 1. 准备工作

```bash
# 确保已安装依赖
pip install -r requirements.txt

# 如果没有 requirements.txt，手动安装：
pip install PyQt5 opencv-python pillow numpy scikit-image torch
```

### 2. 启动游戏

- 打开欢乐斗地主游戏
- 确保游戏窗口可见（不要最小化）

### 3. 运行程序

```bash
# 在项目根目录运行
python main.py
```

### 4. 程序会自动：

1. **查找游戏窗口**
   - 自动检测欢乐斗地主窗口
   - 获取窗口位置和尺寸

2. **等待进入游戏**
   - 检测 Chat 图标
   - 确认已进入游戏界面

3. **游戏循环**
   - 自动识别手牌
   - AI 决策是否叫地主
   - AI 决策出什么牌
   - 自动点击出牌
   - 循环直到游戏结束

## ⚙️ 配置文件

根目录的 `main.py` 使用 `data.json` 作为配置：

```json
{
  "window_class": "UnityWndClass",
  "window_title": "欢乐斗地主",
  "resolution": {
    "width": 1440,
    "height": 810
  }
}
```

## 🔧 常见问题

### Q: 运行 master/main.py 为什么不自动打牌？

**A:** 因为 `master/main.py` 是一个**重构中的新框架**，还没有实现完整的游戏逻辑。

查看代码第 456-459 行：
```python
print("提示: 这是一个演示框架，实际游戏逻辑需要进一步实现")

# TODO: 实现完整的游戏循环
# 1. 叫地主阶段
# 2. 加倍阶段
# 3. 出牌阶段
# 4. 游戏结束处理
```

**解决方案：** 使用根目录的 `main.py`！

### Q: 两个 main.py 有什么区别？

| 特性 | 根目录 `main.py` | `master/main.py` |
|------|------------------|------------------|
| **状态** | ✅ 完整可用 | ❌ 开发中 |
| **功能** | ✅ 全自动打牌 | ❌ 只有框架 |
| **代码行数** | 1500+ 行 | 470 行 |
| **文件大小** | 69KB | 较小 |
| **依赖** | GameHelper, PyQt5 | 重构的模块化架构 |
| **目的** | 实际使用 | 代码重构/学习 |

### Q: master 目录的作用是什么？

**A:** `master/` 是一个**代码重构项目**，目标是：

- ✅ 更模块化的架构
- ✅ 更清晰的代码结构
- ✅ 更好的配置管理（YAML）
- ✅ 更完善的错误处理
- ❌ **但还没完成实际的打牌逻辑**

它可以作为：
- 学习 Python 项目架构的参考
- 未来重构的基础
- 代码规范的示例

**但不能用来自动打牌！**

### Q: 如何让 master/main.py 也能自动打牌？

**A:** 需要实现 `run()` 方法中的 TODO 部分：

```python
def run(self):
    # ... 现有代码 ...

    # TODO: 需要实现这些
    # 1. 叫地主阶段
    #    - 检测叫地主按钮
    #    - AI 决策是否叫
    #    - 点击相应按钮

    # 2. 加倍阶段
    #    - 检测加倍按钮
    #    - AI 决策加倍策略

    # 3. 出牌阶段（主循环）
    while True:
        # - 识别手牌
        # - 识别其他玩家出牌
        # - AI 决策出什么牌
        # - 执行出牌操作
        # - 检测游戏是否结束
        pass

    # 4. 游戏结束处理
    #    - 检测胜利/失败
    #    - 统计数据
    #    - 准备下一局
```

这需要大量的开发工作！

## 🎓 推荐做法

1. **想要自动打牌：** 使用根目录的 `main.py`
   ```bash
   python main.py
   ```

2. **想要学习代码架构：** 研究 `master/` 目录
   ```bash
   # 查看模块化架构
   ls master/

   # 查看配置系统
   cat master/config/androws_config.yaml

   # 查看检测器实现
   cat master/detection/detector.py
   ```

3. **想要测试截图和检测：** 使用 `master/` 的工具脚本
   ```bash
   cd master
   python quick_screenshot.py        # 测试截图
   python check_templates.py         # 检查模板
   python diagnose_screenshot_size.py # 诊断尺寸
   ```

## 📚 总结

- ✅ **自动打牌：** 运行根目录的 `python main.py`
- ❌ **master/main.py：** 只是框架，不能打牌
- 🔧 **master/ 工具：** 可用于调试和测试
- 📖 **学习参考：** master/ 有更好的代码组织

**记住：要自动打牌，运行根目录的 main.py！**

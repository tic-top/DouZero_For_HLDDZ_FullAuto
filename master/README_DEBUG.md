# 调试指南

## 问题：一直显示"未进入游戏"

这个问题通常由以下几个原因造成：

1. **模板文件缺失** - chat.png 或 chat2.png 不存在
2. **窗口分辨率不匹配** - 游戏窗口不是 1440x810
3. **检测区域不正确** - 聊天图标位置变化
4. **模板图片不匹配** - 游戏更新导致图标变化

## 🔍 调试步骤

### 1. 运行调试截图工具

```bash
cd master
python debug_screenshot.py
```

这个工具会：
- ✅ 查找游戏窗口
- ✅ 截取当前游戏画面
- ✅ 在截图上标注所有检测区域（红色框）
- ✅ 保存多个截图文件
- ✅ 自动打开图片查看器

### 2. 查看生成的截图

工具会在 `master/debug_screenshots/` 目录生成以下文件：

```
debug_screenshots/
├── original_game_window.png       # 原始游戏截图
├── annotated_game_window.png      # 标注了所有检测区域的截图
├── region_chat_icon.png           # Chat 图标区域的截图
└── region_my_hand_cards.png       # 手牌区域的截图
```

### 3. 检查 annotated_game_window.png

打开这个文件，查看：

- **红色框** = Chat 图标检测区域
  - 这个区域里是否有聊天图标？
  - 如果没有，说明检测区域配置错误

- **蓝色框** = 手牌区域
- **绿色框** = 其他玩家出牌区域
- **黄色框** = 地主底牌区域

### 4. 检查 region_chat_icon.png

这是从检测区域裁剪出来的图片，应该包含聊天图标。

如果图标位置不对：
1. 记下正确的坐标
2. 修改 `config/default.yaml` 中的 `chat_icon` 区域
3. 重新运行

### 5. 对比模板文件

查看 `pics/chat.png` 和 `pics/chat2.png`，对比实际游戏中的聊天图标：

```bash
# 查看模板文件
ls ../pics/chat*.png
```

如果图标不一致：
1. 从 `region_chat_icon.png` 中裁剪出聊天图标
2. 保存为 `../pics/chat.png` 或 `../pics/chat2.png`
3. 重新运行

## 🛠️ 修复方法

### 方法 1: 调整检测区域

编辑 `master/config/default.yaml`:

```yaml
regions:
  # 修改这个区域的坐标
  chat_icon: [1302, 744, 117, 56]  # [x, y, width, height]
```

运行调试工具确认红色框是否覆盖了聊天图标。

### 方法 2: 更新模板图片

如果游戏更新导致图标变化：

1. 运行 `debug_screenshot.py`
2. 打开 `region_chat_icon.png`
3. 使用图片编辑软件裁剪出聊天图标
4. 保存为 `../pics/chat.png`（覆盖原文件）

### 方法 3: 调整分辨率

如果游戏窗口不是 1440x810：

框架会**自动缩放**坐标，但如果缩放后仍不准确：

1. 在 `config/default.yaml` 中调整基准分辨率：

```yaml
regions:
  base_resolution: [你的游戏宽度, 你的游戏高度]
```

2. 重新标定所有区域坐标

### 方法 4: 降低检测阈值

编辑 `master/config/default.yaml`:

```yaml
detection:
  confidence: 0.75  # 默认 0.8，降低可以提高识别率
```

## 📊 运行主程序查看详细日志

修改后运行主程序：

```bash
cd master
python main.py
```

现在会显示：
- ✓ 已加载的模板列表
- 检测区域坐标
- 每5秒保存一次调试截图
- 详细的检测日志

调试截图会保存在 `master/debug_screenshots/`:
- `waiting_game_0.png` (第0秒)
- `waiting_game_5.png` (第5秒)
- `waiting_game_10.png` (第10秒)
- ...
- `game_started_success.png` (成功时)
- `game_start_failed.png` (失败时)

## 💡 常见问题

### Q1: 找不到游戏窗口

```
❌ 未找到游戏窗口 (class=UnityWndClass, title=欢乐斗地主)
```

**解决方法：**
1. 确保游戏已启动
2. 检查游戏窗口标题是否为"欢乐斗地主"
3. 如果不是，修改配置文件中的 `window_title`

### Q2: 模板文件不存在

```
✗ 模板不存在: C:\...\pics\chat.png
```

**解决方法：**
1. 确认 `pics/` 目录存在
2. 确认 `chat.png` 文件存在
3. 如果不存在，从游戏中截取聊天图标并保存

### Q3: 检测区域不对

打开 `annotated_game_window.png`，如果红色框不在聊天图标位置：

**解决方法：**
1. 测量聊天图标的实际坐标（使用截图工具）
2. 修改 `config/default.yaml` 中的坐标
3. 重新运行

### Q4: 模板匹配失败

即使聊天图标在检测区域内，仍然检测失败：

**原因：**
- 游戏更新导致图标变化
- 图标有动画效果
- 分辨率缩放导致失真

**解决方法：**
1. 截取新的聊天图标模板
2. 降低检测置信度（`confidence: 0.7`）
3. 尝试使用 chat2.png（可能是另一个状态）

## 📝 完整诊断流程

```bash
# 1. 运行调试工具
cd master
python debug_screenshot.py

# 2. 查看生成的截图
# 打开 debug_screenshots/annotated_game_window.png

# 3. 检查模板文件
ls ../pics/chat*.png

# 4. 如果需要，更新配置
# 编辑 config/default.yaml

# 5. 重新运行主程序
python main.py

# 6. 查看调试截图
# 打开 debug_screenshots/ 目录下的所有截图
```

## 🎯 预期结果

成功时，你应该看到：

```
✓ 找到游戏窗口: hwnd=123456, size=1440x810
✓ 已加载模板: chat
✓ 已加载模板: chat2
总计加载 2/2 个 UI 模板

等待进入游戏...
检测区域: (1302, 744, 117, 56)
.....
✓ 已进入游戏！检测到 chat 图标位置: (1320, 760)
[调试] 成功截图已保存: debug_screenshots/game_started_success.png
```

如果还有问题，请查看所有调试截图，分析具体原因！

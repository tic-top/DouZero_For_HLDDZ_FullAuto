# 快速开始 - Androws 欢乐斗地主

## 🎮 你的游戏窗口信息

- **窗口标题**: 欢乐斗地主
- **窗口类名**: Qt5152QWindowIcon
- **窗口尺寸**: 622 x 389
- **进程名称**: Androws.exe

## 📋 快速启动流程

### 1. 检查窗口配置

运行窗口列表工具，确认游戏窗口：

```bash
cd master
python list_windows.py
```

应该能看到"欢乐斗地主"窗口。

### 2. 调试检测区域

运行快速截图工具：

```bash
python quick_screenshot.py
```

这会：
- ✅ 自动找到游戏窗口
- ✅ 截取游戏画面
- ✅ 标注检测区域（红/蓝/绿色框）
- ✅ 保存到 `debug_screenshots/quick_screenshot.png`
- ✅ 自动打开图片查看器

**检查截图中的框框位置是否正确：**
- **红色框** → Chat 图标（右下角）
- **蓝色框** → 你的手牌区域（底部）
- **绿色框** → 按钮区域（中间）

### 3. 调整配置（如果需要）

如果区域位置不对，编辑 `config/androws_config.yaml`：

```yaml
regions:
  # 格式: [x坐标, y坐标, 宽度, 高度]
  chat_icon: [563, 357, 51, 27]      # 调整这里
  my_hand_cards: [78, 269, 453, 43]   # 调整这里
  general_button: [86, 216, 432, 58]  # 调整这里
```

修改后重新运行 `quick_screenshot.py` 查看效果。

### 4. 运行主程序

配置正确后，运行 AI Agent：

```bash
python main.py --config config/androws_config.yaml
```

程序会：
1. 查找游戏窗口
2. 等待进入游戏（检测 Chat 图标）
3. 自动开始游戏流程

## 🛠️ 常用工具

### list_windows.py - 窗口查找工具

列出所有窗口，找到游戏窗口信息：

```bash
python list_windows.py
```

### quick_screenshot.py - 快速截图工具

截取游戏并标注检测区域：

```bash
python quick_screenshot.py
```

### debug_screenshot.py - 完整调试工具

更详细的调试功能（所有区域）：

```bash
python debug_screenshot.py
```

## ⚙️ 配置文件说明

### config/androws_config.yaml

这是专门为你的游戏窗口创建的配置：

```yaml
game:
  window_class: "Qt5152QWindowIcon"  # 窗口类名
  window_title: "欢乐斗地主"          # 窗口标题
  target_resolution:
    width: 622                        # 窗口宽度
    height: 389                       # 窗口高度

regions:
  base_resolution: [622, 389]         # 基准分辨率
  chat_icon: [563, 357, 51, 27]       # Chat 图标位置
  my_hand_cards: [78, 269, 453, 43]   # 手牌区域
  # ... 其他区域
```

## ❓ 常见问题

### Q: 一直显示"未进入游戏"

**原因**: Chat 图标检测失败

**解决**:
1. 运行 `quick_screenshot.py`
2. 查看红色框是否覆盖 Chat 图标
3. 如果不对，调整 `chat_icon` 坐标
4. 降低检测置信度：`detection.confidence: 0.6`

### Q: 找不到游戏窗口

**原因**: 游戏未启动或窗口类名变化

**解决**:
1. 确保游戏已启动
2. 运行 `list_windows.py` 查看窗口信息
3. 更新配置文件中的 `window_class` 和 `window_title`

### Q: 检测区域不准确

**原因**: 坐标配置不对

**解决**:
1. 运行 `quick_screenshot.py` 查看当前区域
2. 使用截图工具（如 Snipping Tool）测量正确坐标
3. 更新 `config/androws_config.yaml` 中的坐标
4. 重新运行 `quick_screenshot.py` 验证

### Q: 模板匹配失败

**原因**: pics/ 目录中的模板图片与游戏不匹配

**解决**:
1. 截取游戏中的 Chat 图标
2. 保存为 `../pics/chat.png`
3. 降低检测置信度

## 📸 截图示例

运行 `quick_screenshot.py` 后，你应该看到类似的截图：

```
┌─────────────────────────────────────┐
│         游戏窗口 (622x389)           │
│                                      │
│  ┌────────────────────────┐         │
│  │     [绿色框]            │         │
│  │     按钮区域            │         │
│  └────────────────────────┘         │
│                                      │
│  ┌──────────────────────────────┐   │
│  │  [蓝色框] 手牌区域           │   │
│  └──────────────────────────────┘   │
│                            ┌──┐     │
│                            │红│Chat │
│                            └──┘     │
└─────────────────────────────────────┘
```

## 🚀 完整工作流程

```bash
# 1. 启动游戏
# （手动打开 Androws 欢乐斗地主）

# 2. 检查窗口
cd master
python list_windows.py

# 3. 调试截图
python quick_screenshot.py
# → 查看 debug_screenshots/quick_screenshot.png
# → 确认红/蓝/绿框位置正确

# 4. 如果需要，调整配置
# 编辑 config/androws_config.yaml

# 5. 运行 AI Agent
python main.py --config config/androws_config.yaml
```

## 💡 提示

1. **确保游戏窗口可见**（不能最小化）
2. **窗口尺寸保持 622x389**（不要缩放）
3. **先用 quick_screenshot.py 验证配置**
4. **Chat 图标是关键**（必须准确）

---

遇到问题请查看 `README_DEBUG.md` 获取更详细的调试指南。

# 截图区域不准确问题的诊断和修复

## 问题描述

你遇到的问题：**区域绘制不准确**

## 根本原因

区域坐标**是动态调整的**，但之前的代码有一个关键错误：

### 错误的做法（之前）

```python
# 1. 获取窗口尺寸
rect = win32gui.GetWindowRect(hwnd)
width = rect[2] - rect[0]   # 例如：622
height = rect[3] - rect[1]  # 例如：389

# 2. 截图
screenshot = capture_window(hwnd)  # 实际尺寸可能是 600x370

# 3. ❌ 错误：用窗口尺寸来缩放坐标
config.set_resolution(width, height)  # 622x389

# 4. 获取区域（基于 622x389 缩放）
x, y, w, h = config.get_region('chat_icon')

# 5. 在截图上绘制（但截图是 600x370）
draw.rectangle([x, y, x+w, y+h])  # ❌ 坐标不匹配！
```

### 问题分析

- `GetWindowRect()` 返回的是**窗口外部边框的尺寸**（包括标题栏、边框）
- `PrintWindow` 或 `ImageGrab.grab` 截取的实际尺寸可能不同：
  - 可能只截取**客户区**（不含边框和标题栏）
  - 可能受 DPI 缩放影响
  - 不同截图方法返回的尺寸可能不一致

示例：
```
窗口尺寸：622 x 389（含边框和标题栏）
客户区：  600 x 370（不含边框）
截图尺寸：600 x 370 或 622 x 389（取决于方法）
```

如果用 622x389 来缩放坐标，但实际截图是 600x370，坐标就会偏移！

## 解决方案

### 正确的做法（修复后）

```python
# 1. 获取窗口尺寸
rect = win32gui.GetWindowRect(hwnd)
window_width = rect[2] - rect[0]
window_height = rect[3] - rect[1]

# 2. 截图
screenshot = capture_window(hwnd)

# 3. ✅ 正确：用截图的实际尺寸来缩放坐标
actual_width, actual_height = screenshot.size
config.set_resolution(actual_width, actual_height)

# 4. 检测尺寸差异
if (actual_width, actual_height) != (window_width, window_height):
    print(f"警告: 截图尺寸与窗口尺寸不一致")

# 5. 获取区域（基于实际截图尺寸缩放）
x, y, w, h = config.get_region('chat_icon')

# 6. 在截图上绘制（坐标完全匹配）
draw.rectangle([x, y, x+w, y+h])  # ✅ 准确！
```

## 坐标缩放原理

配置文件中的坐标是基于基准分辨率的：

```yaml
# config/androws_config.yaml
regions:
  base_resolution: [622, 389]  # 基准分辨率
  chat_icon: [563, 357, 51, 27]  # 基准坐标
```

动态缩放公式（`config_loader.py:102-112`）：

```python
# 基准分辨率
base_width, base_height = 622, 389

# 当前实际分辨率（截图尺寸）
curr_width, curr_height = screenshot.size

# 缩放比例
scale_x = curr_width / base_width   # 例如：600/622 = 0.965
scale_y = curr_height / base_height # 例如：370/389 = 0.951

# 缩放后的坐标
x_scaled = int(x * scale_x)  # 563 * 0.965 = 543
y_scaled = int(y * scale_y)  # 357 * 0.951 = 339
```

## 已修复的文件

### 1. `master/quick_screenshot.py`

- ✅ 使用 `screenshot.size` 而不是窗口尺寸
- ✅ 添加尺寸差异警告
- ✅ 显示详细的诊断信息

### 2. `master/main.py`

- ✅ 在 `find_game_window()` 中进行测试截图
- ✅ 使用截图实际尺寸设置分辨率
- ✅ 在 `wait_for_game_start()` 中使用正确的截图方法

### 3. `master/diagnose_screenshot_size.py`（新增）

诊断工具，用于检查：
- 窗口尺寸 vs 客户区尺寸
- GDI 截图尺寸 vs ImageGrab 截图尺寸
- 尺寸差异的具体数值

## 如何验证修复

### 1. 运行诊断工具

```bash
cd master
python diagnose_screenshot_size.py
```

输出示例：
```
[1] 查找窗口...
✓ 找到窗口（类名）: Qt5152QWindowIcon

[2] 窗口信息...
  窗口大小: 622 x 389
  客户区大小: 600 x 370
  边框+标题栏: 22 x 19

[3] 方法 1: GDI (PrintWindow) 截图...
  截图尺寸: 622 x 389
  ✓ 与窗口大小一致

[4] 方法 2: ImageGrab 截图...
  截图尺寸: 622 x 389
  ✓ 与窗口大小一致
```

### 2. 运行 quick_screenshot.py

```bash
cd master
python quick_screenshot.py
```

检查输出：
```
[2] 查找游戏窗口...
    [OK] 找到窗口: 622x389

[3] 截取游戏窗口...
    ✓ 使用 GDI 方法截图成功
    [OK] 截图成功: 622x389
    # 如果尺寸不一致，会显示警告

[4] 绘制检测区域...
    Chat 区域: (543, 339, 49, 25)  # 缩放后的坐标
```

### 3. 查看截图

打开 `debug_screenshots/quick_screenshot.png`，检查：
- 红色框是否准确框住 Chat 图标
- 蓝色框是否准确框住手牌区域
- 绿色框是否准确框住按钮区域

## 常见问题

### Q1: 为什么窗口尺寸和截图尺寸会不一致？

**A:** 主要原因：
1. **边框和标题栏**：`GetWindowRect` 包含边框，但有些截图方法只截取客户区
2. **DPI 缩放**：高 DPI 显示器可能导致坐标缩放
3. **截图方法差异**：PrintWindow 和 ImageGrab 可能返回不同尺寸

### Q2: 应该用哪种截图方法？

**A:** 使用 `method="auto"`（默认）：
- 优先尝试 GDI (PrintWindow)：不受窗口遮挡影响
- 失败时回退到 ImageGrab：对硬件加速窗口更稳定
- 自动选择最佳方法

### Q3: 如果区域还是不准确怎么办？

**A:** 按以下步骤排查：

1. 运行诊断工具确认尺寸
   ```bash
   python diagnose_screenshot_size.py
   ```

2. 检查配置文件中的 `base_resolution` 是否正确
   ```yaml
   regions:
     base_resolution: [622, 389]  # 应该与截图尺寸一致
   ```

3. 使用 `debug_screenshot.py` 重新标定坐标
   ```bash
   python debug_screenshot.py
   ```

4. 查看调试截图中的坐标标注

## 技术细节

### 截图方法对比

| 方法 | 优点 | 缺点 | 尺寸 |
|------|------|------|------|
| **PrintWindow (GDI)** | 不受遮挡影响 | 某些窗口返回黑屏 | 通常是窗口尺寸 |
| **ImageGrab** | 稳定性好 | 受遮挡影响 | 窗口尺寸 |
| **BitBlt** | 速度快 | 受遮挡影响，需前台 | 客户区尺寸 |

### 坐标系统

```
┌─────────────────────────────────────┐  ← 窗口边框 (0, 0)
│ 标题栏：欢乐斗地主                  │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │                                 │ │  ← 客户区 (0, 0)
│ │    游戏内容                      │ │
│ │                                 │ │
│ │                   [Chat Icon]   │ │  ← (563, 357) 基于客户区
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 总结

**问题**：区域不准确
**原因**：用窗口尺寸缩放坐标，但在截图（可能是客户区尺寸）上绘制
**解决**：用截图的实际尺寸来缩放坐标

现在区域坐标是**根据截图实际大小动态调整的**，应该非常准确了！

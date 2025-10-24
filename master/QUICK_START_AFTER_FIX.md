# 修复后的快速使用指南

## 🎯 修复内容总结

已修复**区域绘制不准确**问题，现在坐标会根据截图实际尺寸动态调整。

## 🚀 快速验证修复

### 1️⃣ 诊断窗口和截图尺寸

```bash
cd master
python diagnose_screenshot_size.py
```

**查看输出：**
- 窗口尺寸 vs 截图尺寸是否一致？
- 如果不一致，差异是多少？

### 2️⃣ 测试坐标修复效果

```bash
python test_screenshot_fix.py
```

**查看生成的截图：**
- `debug_screenshots/test_wrong.png` - 红框（使用窗口尺寸，可能偏移）
- `debug_screenshots/test_correct.png` - 绿框（使用截图尺寸，应该准确）

**对比检查：**
- 红框是否偏移？
- 绿框是否准确框住 Chat 图标？

### 3️⃣ 运行快速截图工具

```bash
python quick_screenshot.py
```

**查看输出：**
```
[3] 截取游戏窗口...
    ✓ 使用 GDI 方法截图成功
    [OK] 截图成功: 600x370
    [!] 警告: 截图尺寸与窗口尺寸不一致  ← 如果出现这行，说明修复生效了
        窗口: 622x389
        截图: 600x370

[4] 绘制检测区域...
    Chat 区域: (543, 339, 49, 25)  ← 这是缩放后的正确坐标
```

**查看截图：**
- 打开 `debug_screenshots/quick_screenshot.png`
- 检查红框、蓝框、绿框是否准确

## 📊 预期结果

### ✅ 成功的标志

1. **quick_screenshot.png 中的框准确无误**
   - 红框准确框住 Chat 图标
   - 蓝框准确框住手牌区域
   - 绿框准确框住按钮区域

2. **test_correct.png 的绿框准确**
   - 绿框正好框住 Chat 图标
   - 即使 test_wrong.png 的红框偏移了

3. **控制台输出正常**
   - 显示截图尺寸和窗口尺寸
   - 如果不一致，会有警告提示
   - 区域坐标自动缩放

### ❌ 如果还是不准确

如果区域还是偏移，按以下步骤排查：

#### 1. 检查配置文件的基准分辨率

打开 `config/androws_config.yaml`：

```yaml
regions:
  base_resolution: [622, 389]  # ← 这个应该是你标定坐标时的窗口尺寸
```

**如何确定正确的基准分辨率？**

运行 `diagnose_screenshot_size.py`，查看输出：
```
截图尺寸: 600 x 370
```

然后修改配置文件：
```yaml
regions:
  base_resolution: [600, 370]  # ← 改成截图尺寸
```

#### 2. 重新标定坐标

如果改了基准分辨率，需要重新标定所有坐标：

```bash
python debug_screenshot.py
```

查看生成的截图，手动记录各区域的坐标，更新配置文件。

#### 3. 检查是否使用了正确的配置文件

确保代码加载的是正确的配置：

```python
# quick_screenshot.py
config = get_config('config/androws_config.yaml')  # ← 确认路径正确
```

## 🔧 修改的关键代码

### 核心改进

**修改前（错误）：**
```python
# 获取窗口尺寸
rect = win32gui.GetWindowRect(hwnd)
width = rect[2] - rect[0]
height = rect[3] - rect[1]

# 截图
screenshot = ImageGrab.grab(bbox=rect)

# ❌ 用窗口尺寸设置分辨率
config.set_resolution(width, height)

# 获取区域并绘制
region = config.get_region('chat_icon')
draw.rectangle(region, screenshot)  # ❌ 坐标不匹配
```

**修改后（正确）：**
```python
# 截图
screenshot = capture_window(hwnd, method="auto")

# ✅ 用截图实际尺寸设置分辨率
actual_width, actual_height = screenshot.size
config.set_resolution(actual_width, actual_height)

# 获取区域并绘制
region = config.get_region('chat_icon')
draw.rectangle(region, screenshot)  # ✅ 完美匹配
```

### 在 main.py 中的应用

**find_game_window():**
```python
# 进行测试截图
test_screenshot = capture_window(hwnd, method="auto")

# 使用截图实际尺寸
self._update_resolution_from_screenshot(test_screenshot)
```

**wait_for_game_start():**
```python
for i in range(max_attempts):
    # 每次循环都重新截图
    screenshot = capture_window(self.window_handle, method="auto")

    # 每次都更新分辨率（重要！）
    self._update_resolution_from_screenshot(screenshot)

    # 重新获取区域（会根据新的分辨率计算）
    chat_region = self.config.get_region('chat_icon')

    # 检测
    chat_pos = self.ui_detector.detect(screenshot, 'chat', region=chat_region)
```

## 📝 关键注意事项

### ⚠️ 每次截图后必须更新分辨率

```python
# ❌ 错误：只在开始时设置一次
config.set_resolution(width, height)

for i in range(100):
    screenshot = capture_window(hwnd)
    region = config.get_region('chat_icon')  # ❌ 使用的是旧分辨率

# ✅ 正确：每次截图后都更新
for i in range(100):
    screenshot = capture_window(hwnd)
    config.set_resolution(*screenshot.size)  # ✅
    region = config.get_region('chat_icon')  # ✅ 使用新分辨率
```

### ⚠️ 不要混用窗口尺寸和截图

```python
# ❌ 错误
window_rect = win32gui.GetWindowRect(hwnd)
window_width = window_rect[2] - window_rect[0]
screenshot = capture_window(hwnd)
config.set_resolution(window_width, window_height)  # ❌

# ✅ 正确
screenshot = capture_window(hwnd)
config.set_resolution(*screenshot.size)  # ✅
```

### ⚠️ base_resolution 必须匹配

```yaml
# 如果你的截图尺寸是 600x370
regions:
  base_resolution: [600, 370]  # ✅ 匹配

  # 所有坐标都应该是基于 600x370 标定的
  chat_icon: [543, 339, 49, 25]
```

## 🎓 工作原理

### 动态缩放公式

```
实际坐标 = 基准坐标 × (当前尺寸 / 基准尺寸)
```

**示例：**

```yaml
# 配置文件
regions:
  base_resolution: [622, 389]
  chat_icon: [563, 357, 51, 27]
```

**当窗口尺寸 = 622x389 时：**
```python
scale_x = 622 / 622 = 1.0
scale_y = 389 / 389 = 1.0

实际坐标 = [563×1.0, 357×1.0, 51×1.0, 27×1.0]
        = [563, 357, 51, 27]  # 不缩放
```

**当截图尺寸 = 600x370 时（客户区）：**
```python
scale_x = 600 / 622 = 0.965
scale_y = 370 / 389 = 0.951

实际坐标 = [563×0.965, 357×0.951, 51×0.965, 27×0.951]
        = [543, 339, 49, 25]  # 缩放后
```

这样，无论窗口大小如何变化，坐标都能准确对应到截图上！

## 📚 相关文档

- **[README_SCREENSHOT_FIX.md](README_SCREENSHOT_FIX.md)** - 详细的技术说明
- **[CHANGELOG_SCREENSHOT_FIX.md](CHANGELOG_SCREENSHOT_FIX.md)** - 完整的修改日志

## 🐛 遇到问题？

1. 运行 `diagnose_screenshot_size.py` 检查尺寸
2. 运行 `test_screenshot_fix.py` 对比效果
3. 检查配置文件的 `base_resolution`
4. 查看调试截图确认区域位置

## ✅ 总结

修复后的系统能够：
- ✅ 自动检测截图和窗口尺寸差异
- ✅ 根据实际截图尺寸动态缩放坐标
- ✅ 提供详细的诊断信息
- ✅ 兼容各种窗口状态和截图方法

**现在区域应该非常准确了！** 🎉

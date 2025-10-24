# 截图尺寸修复日志

## 修改日期
2025-01-XX

## 问题描述
区域绘制不准确，坐标偏移。

## 根本原因
代码使用**窗口尺寸**来缩放坐标，但在**截图**（尺寸可能不同）上绘制，导致坐标不匹配。

```python
# 错误的流程
窗口尺寸 = GetWindowRect()  # 622x389 (含边框)
截图 = capture_window()      # 600x370 (只有客户区)
config.set_resolution(窗口尺寸)  # ❌ 用 622x389 缩放
坐标 = config.get_region()
在截图上绘制(坐标)             # ❌ 在 600x370 上用 622x389 的坐标
```

## 修复方案
使用**截图的实际尺寸**来缩放坐标。

```python
# 正确的流程
截图 = capture_window()
实际尺寸 = 截图.size         # 600x370
config.set_resolution(实际尺寸)  # ✅ 用 600x370 缩放
坐标 = config.get_region()
在截图上绘制(坐标)             # ✅ 完美匹配
```

## 修改的文件

### 1. `master/main.py`

#### 新增方法

**`_update_resolution_from_screenshot(screenshot)`** (行 240-255)

封装分辨率更新逻辑，避免重复代码。

```python
def _update_resolution_from_screenshot(self, screenshot) -> bool:
    """根据截图更新分辨率配置"""
    if screenshot is None:
        return False

    actual_width, actual_height = screenshot.size
    self.config.set_resolution(actual_width, actual_height)
    return True
```

#### 修改方法 1: `find_game_window()` (行 257-310)

**修改前：**
```python
rect = win32gui.GetWindowRect(hwnd)
width = rect[2] - rect[0]
height = rect[3] - rect[1]
config.set_resolution(width, height)  # ❌
```

**修改后：**
```python
rect = win32gui.GetWindowRect(hwnd)
window_width = rect[2] - rect[0]
window_height = rect[3] - rect[1]

# 进行测试截图获取实际尺寸
test_screenshot = capture_window(hwnd, method="auto")
if test_screenshot:
    self._update_resolution_from_screenshot(test_screenshot)  # ✅
    actual_width, actual_height = test_screenshot.size

    if (actual_width, actual_height) != (window_width, window_height):
        print(f"注意: 截图尺寸({actual_width}x{actual_height}) != 窗口尺寸({window_width}x{window_height})")
```

**改进点：**
- ✅ 使用截图实际尺寸设置分辨率
- ✅ 检测并提示尺寸差异
- ✅ 提供详细的调试信息

#### 修改方法 2: `wait_for_game_start()` (行 312-407)

**修改前：**
```python
# 在循环外获取区域（只计算一次）
chat_region = self.config.get_region('chat_icon')

for i in range(max_attempts):
    screenshot = ImageGrab.grab(...)
    # 使用固定的 chat_region ❌
    chat_pos = self.ui_detector.detect(screenshot, 'chat', region=chat_region)
```

**修改后：**
```python
# 删除循环外的区域获取

for i in range(max_attempts):
    screenshot = capture_window(self.window_handle, method="auto")

    # 每次截图后更新分辨率 ✅
    self._update_resolution_from_screenshot(screenshot)

    # 重新获取区域（根据当前分辨率） ✅
    chat_region = self.config.get_region('chat_icon')

    # 首次输出信息
    if i == 0:
        print(f"截图尺寸: {screenshot.size}")
        print(f"检测区域: {chat_region}")

    # 检测
    chat_pos = self.ui_detector.detect(screenshot, 'chat', region=chat_region)
```

**改进点：**
- ✅ 每次截图后立即更新分辨率
- ✅ 每次重新计算区域坐标
- ✅ 使用健壮的 `capture_window()` 方法
- ✅ 添加首次调试信息输出

### 2. `master/quick_screenshot.py`

#### 修改主函数 (行 191-216)

**修改前：**
```python
rect = win32gui.GetWindowRect(hwnd)
width = rect[2] - rect[0]
height = rect[3] - rect[1]

screenshot = capture_window(hwnd)
config.set_resolution(width, height)  # ❌
```

**修改后：**
```python
rect = win32gui.GetWindowRect(hwnd)
window_width = rect[2] - rect[0]
window_height = rect[3] - rect[1]

screenshot = capture_window(hwnd, method="auto")
actual_width, actual_height = screenshot.size  # ✅

# 检查尺寸差异
if (actual_width, actual_height) != (window_width, window_height):
    print(f"[!] 警告: 截图尺寸与窗口尺寸不一致")
    print(f"    窗口: {window_width}x{window_height}")
    print(f"    截图: {actual_width}x{actual_height}")

# 使用截图实际尺寸 ✅
config.set_resolution(actual_width, actual_height)
```

**改进点：**
- ✅ 使用截图实际尺寸
- ✅ 检测并警告尺寸差异
- ✅ 输出详细的诊断信息

### 3. 新增诊断工具

#### `master/diagnose_screenshot_size.py`

用于诊断窗口尺寸和截图尺寸的差异。

**输出信息：**
- 窗口尺寸 vs 客户区尺寸
- GDI 截图尺寸
- ImageGrab 截图尺寸
- 两种方法的对比
- 保存测试截图

**使用方法：**
```bash
cd master
python diagnose_screenshot_size.py
```

#### `master/test_screenshot_fix.py`

验证修复是否有效的测试脚本。

**测试内容：**
- 对比使用窗口尺寸 vs 截图尺寸计算坐标
- 生成两张对比截图（红框=错误，绿框=正确）
- 输出坐标差异

**使用方法：**
```bash
cd master
python test_screenshot_fix.py
```

#### `master/README_SCREENSHOT_FIX.md`

详细的问题说明和修复文档。

## 技术细节

### 为什么窗口尺寸 ≠ 截图尺寸？

| 因素 | 说明 |
|------|------|
| **边框和标题栏** | `GetWindowRect` 包含边框，某些截图方法只截取客户区 |
| **DPI 缩放** | 高 DPI 显示器可能导致坐标缩放 |
| **截图方法差异** | PrintWindow vs ImageGrab vs BitBlt 返回的尺寸可能不同 |

### 截图方法对比

| 方法 | 包含内容 | 典型尺寸 |
|------|----------|----------|
| **GetWindowRect** | 窗口+边框+标题栏 | 622x389 |
| **GetClientRect** | 仅客户区 | 600x370 |
| **PrintWindow (GDI)** | 通常是窗口全部 | 622x389 或 600x370 |
| **ImageGrab** | 屏幕对应区域 | 622x389 |

### 坐标缩放公式

```python
# 配置文件中的基准坐标
base_resolution = [622, 389]
chat_icon = [563, 357, 51, 27]

# 当前实际尺寸（截图尺寸）
current_resolution = screenshot.size  # 例如 (600, 370)

# 缩放比例
scale_x = current_width / base_width    # 600/622 = 0.965
scale_y = current_height / base_height  # 370/389 = 0.951

# 缩放后的坐标
x = int(563 * 0.965) = 543
y = int(357 * 0.951) = 339
w = int(51 * 0.965) = 49
h = int(27 * 0.951) = 25

# 结果
chat_icon_scaled = [543, 339, 49, 25]
```

## 测试验证

### 1. 运行诊断工具

```bash
python master/diagnose_screenshot_size.py
```

**期望输出：**
```
[2] 窗口信息...
  窗口大小: 622 x 389
  客户区大小: 600 x 370
  边框+标题栏: 22 x 19

[3] 方法 1: GDI (PrintWindow) 截图...
  截图尺寸: 622 x 389
  ✓ 与窗口大小一致

诊断结果:
✓ 两种截图方法尺寸一致
```

### 2. 运行测试脚本

```bash
python master/test_screenshot_fix.py
```

**期望输出：**
```
[4] 尺寸对比...
  ⚠ 尺寸不一致！
    窗口: 622x389
    截图: 600x370
    差异: 22x19

[5] 测试坐标缩放...
  方式 A（错误）: chat_icon 区域: (563, 357, 51, 27)
  方式 B（正确）: chat_icon 区域: (543, 339, 49, 25)
  ⚠ 两种方式产生的坐标不同！
    差异 x: -20
    差异 y: -18
```

查看生成的截图：
- `test_wrong.png`: 红框偏移
- `test_correct.png`: 绿框准确

### 3. 运行 quick_screenshot

```bash
python master/quick_screenshot.py
```

**期望输出：**
```
[3] 截取游戏窗口...
    ✓ 使用 GDI 方法截图成功
    [OK] 截图成功: 600x370
    [!] 警告: 截图尺寸与窗口尺寸不一致
        窗口: 622x389
        截图: 600x370

[4] 绘制检测区域...
    Chat 区域: (543, 339, 49, 25)
    手牌区域: (75, 256, 435, 41)
    按钮区域: (83, 206, 415, 55)
```

查看 `debug_screenshots/quick_screenshot.png`，检查区域框是否准确。

## 影响范围

### 受益的功能

- ✅ 区域检测准确性
- ✅ UI 元素定位
- ✅ 卡牌识别
- ✅ 按钮点击
- ✅ 所有基于坐标的操作

### 兼容性

- ✅ 兼容不同窗口尺寸
- ✅ 兼容不同 DPI 设置
- ✅ 兼容不同截图方法
- ✅ 向后兼容（窗口尺寸==截图尺寸时，行为不变）

## 注意事项

1. **配置文件的 base_resolution 必须正确**
   ```yaml
   regions:
     base_resolution: [622, 389]  # 应该是你标定坐标时的窗口尺寸
   ```

2. **每次截图后必须更新分辨率**
   ```python
   screenshot = capture_window(hwnd)
   config.set_resolution(screenshot.size[0], screenshot.size[1])  # 必须
   region = config.get_region('chat_icon')  # 在更新分辨率之后
   ```

3. **不要混用窗口尺寸和截图尺寸**
   ```python
   # ❌ 错误
   window_size = GetWindowRect()
   screenshot = capture_window()
   config.set_resolution(*window_size)
   draw.rectangle(config.get_region(), screenshot)

   # ✅ 正确
   screenshot = capture_window()
   config.set_resolution(*screenshot.size)
   draw.rectangle(config.get_region(), screenshot)
   ```

## 总结

本次修复解决了一个核心问题：**坐标系统不匹配**。

通过确保始终使用**截图的实际尺寸**来计算坐标，无论截图方法、窗口状态、DPI 设置如何变化，坐标都能保持准确。

这是一个**架构级别**的修复，影响所有基于坐标的功能，极大提升了系统的健壮性和准确性。

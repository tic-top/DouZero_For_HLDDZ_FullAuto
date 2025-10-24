"""
测试脚本：验证截图尺寸修复
"""
import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import win32gui
from master.utils import get_config
from PIL import ImageDraw


def resolve_handle(window_class=None, window_title=None):
    """查找窗口"""
    import win32gui

    if window_class:
        handle = win32gui.FindWindow(window_class, None)
        if handle:
            return handle

    if window_title:
        handle = win32gui.FindWindow(None, window_title)
        if handle:
            return handle

    candidate_titles = [window_title] if window_title else ["欢乐斗地主"]
    matches = []

    def enum_handler(hwnd, results):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if any(keyword in title for keyword in candidate_titles):
            results.append(hwnd)

    win32gui.EnumWindows(enum_handler, matches)
    return matches[0] if matches else None


def capture_window(hwnd):
    """简化的截图函数"""
    import win32ui
    from ctypes import windll
    from PIL import Image

    try:
        windll.user32.SetProcessDPIAware()
    except:
        pass

    rect = win32gui.GetWindowRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)

    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    im = Image.frombuffer(
        "RGB",
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1
    )

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    return im


def main():
    print("=" * 80)
    print("截图尺寸修复验证测试")
    print("=" * 80)

    # 加载配置
    config_path = 'config/androws_config.yaml'
    print(f"\n[1] 加载配置: {config_path}")
    config = get_config(config_path)

    window_class = config.get('game.window_class')
    window_title = config.get('game.window_title')

    # 查找窗口
    print(f"\n[2] 查找窗口...")
    hwnd = resolve_handle(window_class, window_title)
    if not hwnd:
        print("✗ 未找到窗口，请先打开游戏")
        return

    # 获取窗口尺寸
    rect = win32gui.GetWindowRect(hwnd)
    window_width = rect[2] - rect[0]
    window_height = rect[3] - rect[1]
    print(f"  窗口尺寸: {window_width}x{window_height}")

    # 截图
    print(f"\n[3] 截图...")
    screenshot = capture_window(hwnd)
    actual_width, actual_height = screenshot.size
    print(f"  截图尺寸: {actual_width}x{actual_height}")

    # 检查尺寸差异
    print(f"\n[4] 尺寸对比...")
    if (actual_width, actual_height) == (window_width, window_height):
        print("  ✓ 窗口尺寸和截图尺寸一致")
    else:
        print(f"  ⚠ 尺寸不一致！")
        print(f"    窗口: {window_width}x{window_height}")
        print(f"    截图: {actual_width}x{actual_height}")
        print(f"    差异: {window_width - actual_width}x{window_height - actual_height}")

    # 测试坐标缩放 - 错误的方式
    print(f"\n[5] 测试坐标缩放...")

    print(f"\n  方式 A（错误）: 使用窗口尺寸设置分辨率")
    config.set_resolution(window_width, window_height)
    region_wrong = config.get_region('chat_icon')
    print(f"    chat_icon 区域: {region_wrong}")

    print(f"\n  方式 B（正确）: 使用截图尺寸设置分辨率")
    config.set_resolution(actual_width, actual_height)
    region_correct = config.get_region('chat_icon')
    print(f"    chat_icon 区域: {region_correct}")

    if region_wrong != region_correct:
        print(f"\n  ⚠ 两种方式产生的坐标不同！")
        print(f"    差异 x: {region_correct[0] - region_wrong[0]}")
        print(f"    差异 y: {region_correct[1] - region_wrong[1]}")
    else:
        print(f"\n  ✓ 两种方式产生的坐标相同（窗口尺寸==截图尺寸）")

    # 绘制对比图
    print(f"\n[6] 生成对比截图...")

    # 使用错误的坐标
    img_wrong = screenshot.copy()
    config.set_resolution(window_width, window_height)
    draw = ImageDraw.Draw(img_wrong)
    x, y, w, h = config.get_region('chat_icon')
    draw.rectangle([x, y, x+w, y+h], outline='red', width=3)
    draw.text((x, y-20), 'WRONG (window size)', fill='red')

    # 使用正确的坐标
    img_correct = screenshot.copy()
    config.set_resolution(actual_width, actual_height)
    draw = ImageDraw.Draw(img_correct)
    x, y, w, h = config.get_region('chat_icon')
    draw.rectangle([x, y, x+w, y+h], outline='green', width=3)
    draw.text((x, y-20), 'CORRECT (screenshot size)', fill='green')

    # 保存
    if not os.path.exists('debug_screenshots'):
        os.makedirs('debug_screenshots')

    img_wrong.save('debug_screenshots/test_wrong.png')
    img_correct.save('debug_screenshots/test_correct.png')

    print(f"  已保存: debug_screenshots/test_wrong.png (红框)")
    print(f"  已保存: debug_screenshots/test_correct.png (绿框)")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

    print("\n请查看两张截图：")
    print("  - test_wrong.png: 使用窗口尺寸计算坐标（可能不准）")
    print("  - test_correct.png: 使用截图尺寸计算坐标（准确）")
    print("\n如果红框偏移，绿框准确，说明修复有效！")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

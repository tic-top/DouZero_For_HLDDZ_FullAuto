"""
诊断工具：检查截图尺寸和窗口尺寸是否一致
"""
import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import win32gui
import win32ui
from ctypes import windll
from PIL import Image, ImageGrab, ImageDraw


def find_window():
    """查找窗口"""
    # 尝试多种方法
    class_names = ["Qt5152QWindowIcon", "UnityWndClass"]
    titles = ["欢乐斗地主"]

    for class_name in class_names:
        hwnd = win32gui.FindWindow(class_name, None)
        if hwnd:
            print(f"✓ 找到窗口（类名）: {class_name}")
            return hwnd

    for title in titles:
        hwnd = win32gui.FindWindow(None, title)
        if hwnd:
            print(f"✓ 找到窗口（标题）: {title}")
            return hwnd

    print("✗ 未找到窗口")
    return None


def capture_with_gdi(hwnd):
    """使用 GDI 方法截图"""
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
    print("截图尺寸诊断工具")
    print("=" * 80)

    # 查找窗口
    print("\n[1] 查找窗口...")
    hwnd = find_window()
    if not hwnd:
        print("请先打开游戏窗口")
        return

    # 获取窗口信息
    print("\n[2] 窗口信息...")
    rect = win32gui.GetWindowRect(hwnd)
    window_width = rect[2] - rect[0]
    window_height = rect[3] - rect[1]

    print(f"  窗口句柄: {hwnd}")
    print(f"  窗口标题: {win32gui.GetWindowText(hwnd)}")
    print(f"  窗口类名: {win32gui.GetClassName(hwnd)}")
    print(f"  窗口位置: ({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]})")
    print(f"  窗口大小: {window_width} x {window_height}")

    # 获取客户区大小
    client_rect = win32gui.GetClientRect(hwnd)
    client_width = client_rect[2] - client_rect[0]
    client_height = client_rect[3] - client_rect[1]
    print(f"\n  客户区大小: {client_width} x {client_height}")
    print(f"  边框+标题栏: {window_width - client_width} x {window_height - client_height}")

    # 方法 1: GDI 截图
    print("\n[3] 方法 1: GDI (PrintWindow) 截图...")
    try:
        img_gdi = capture_with_gdi(hwnd)
        print(f"  截图尺寸: {img_gdi.size[0]} x {img_gdi.size[1]}")

        if img_gdi.size == (window_width, window_height):
            print("  ✓ 与窗口大小一致")
        elif img_gdi.size == (client_width, client_height):
            print("  ⚠ 与客户区大小一致（不含边框）")
        else:
            print("  ✗ 尺寸不一致！")

        # 保存
        img_gdi.save("debug_screenshots/test_gdi.png")
        print("  已保存: debug_screenshots/test_gdi.png")
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        img_gdi = None

    # 方法 2: ImageGrab 截图
    print("\n[4] 方法 2: ImageGrab 截图...")
    try:
        img_grab = ImageGrab.grab(bbox=rect)
        print(f"  截图尺寸: {img_grab.size[0]} x {img_grab.size[1]}")

        if img_grab.size == (window_width, window_height):
            print("  ✓ 与窗口大小一致")
        elif img_grab.size == (client_width, client_height):
            print("  ⚠ 与客户区大小一致（不含边框）")
        else:
            print("  ✗ 尺寸不一致！")

        # 保存
        img_grab.save("debug_screenshots/test_grab.png")
        print("  已保存: debug_screenshots/test_grab.png")
    except Exception as e:
        print(f"  ✗ 失败: {e}")
        img_grab = None

    # 比较两种方法
    print("\n" + "=" * 80)
    print("诊断结果")
    print("=" * 80)

    if img_gdi and img_grab:
        if img_gdi.size == img_grab.size:
            print("✓ 两种截图方法尺寸一致")
        else:
            print("✗ 两种截图方法尺寸不一致！")
            print(f"  GDI:  {img_gdi.size}")
            print(f"  Grab: {img_grab.size}")

    print("\n建议:")
    print("1. 如果截图尺寸 != 窗口大小，需要修改代码使用截图的实际尺寸")
    print("2. 建议使用: config.set_resolution(screenshot.size[0], screenshot.size[1])")
    print("3. 而不是:    config.set_resolution(window_width, window_height)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        # 创建输出目录
        if not os.path.exists("debug_screenshots"):
            os.makedirs("debug_screenshots")

        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

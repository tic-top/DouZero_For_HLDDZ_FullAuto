"""
截取指定窗口 - 使用多种方法
"""
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import win32gui
import win32ui
import win32con
from ctypes import windll
from PIL import Image, ImageGrab
import os


def capture_with_printwindow(hwnd):
    """方法1: 使用 PrintWindow API"""
    try:
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        if width <= 0 or height <= 0:
            return None

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        # PW_RENDERFULLCONTENT = 2, PW_CLIENTONLY = 1
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return im if result == 1 else None
    except Exception as e:
        print(f"  [!] PrintWindow 失败: {e}")
        return None


def capture_with_bitblt(hwnd):
    """方法2: 使用 BitBlt"""
    try:
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return im
    except Exception as e:
        print(f"  [!] BitBlt 失败: {e}")
        return None


def capture_with_screengrab(hwnd):
    """方法3: 使用屏幕截图"""
    try:
        rect = win32gui.GetWindowRect(hwnd)
        return ImageGrab.grab(bbox=rect)
    except Exception as e:
        print(f"  [!] ScreenGrab 失败: {e}")
        return None


def main():
    print("=" * 80)
    print("  截取指定窗口工具")
    print("=" * 80)

    # 窗口 7 的句柄
    hwnd = 262412  # Chrome_WidgetWin_0

    print(f"\n目标窗口句柄: {hwnd}")

    try:
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        is_visible = win32gui.IsWindowVisible(hwnd)

        print(f"  标题: {title or '(无标题)'}")
        print(f"  类名: {class_name}")
        print(f"  尺寸: {width} x {height}")
        print(f"  可见: {is_visible}")
        print(f"  位置: {rect}")
    except Exception as e:
        print(f"[!] 获取窗口信息失败: {e}")
        return

    output_dir = 'specific_window_captures'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 尝试多种截图方法
    methods = [
        ('PrintWindow (全内容)', capture_with_printwindow),
        ('BitBlt', capture_with_bitblt),
        ('ScreenGrab', capture_with_screengrab),
    ]

    print(f"\n正在尝试多种截图方法...\n")

    for method_name, method_func in methods:
        print(f"[{method_name}]")
        img = method_func(hwnd)

        if img:
            filename = f"{method_name.replace(' ', '_').replace('(', '').replace(')', '')}.png"
            filepath = os.path.join(output_dir, filename)
            img.save(filepath)
            print(f"  [OK] 已保存: {filepath}")
            print(f"  尺寸: {img.size}")
        else:
            print(f"  [X] 失败")

        print()

    print("=" * 80)
    print(f"所有截图已保存到: {os.path.abspath(output_dir)}")
    print("=" * 80)

    # 打开目录
    try:
        os.startfile(os.path.abspath(output_dir))
        print("\n[OK] 已打开截图目录")
    except:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

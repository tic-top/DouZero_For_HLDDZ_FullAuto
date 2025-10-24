"""
截取所有 Androws.exe 窗口 - 简单直接版
"""
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import win32gui
import win32ui
import win32con
import win32process
from ctypes import windll
from PIL import Image, ImageGrab, ImageDraw, ImageFont
import psutil
import os


def get_all_androws_windows():
    """获取所有 Androws.exe 的窗口"""
    all_windows = []

    def callback(hwnd, results):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)

            if 'Androws' in process.name():
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                is_visible = win32gui.IsWindowVisible(hwnd)

                all_windows.append({
                    'hwnd': hwnd,
                    'title': title or '(无标题)',
                    'class_name': class_name,
                    'width': width,
                    'height': height,
                    'is_visible': is_visible,
                    'rect': rect
                })
        except:
            pass

        return True

    win32gui.EnumWindows(callback, all_windows)
    return all_windows


def capture_multiple_methods(hwnd, rect):
    """使用多种方法截图"""
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]

    images = []

    # 方法1: BitBlt
    try:
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        images.append(('BitBlt', im))
    except Exception as e:
        print(f"    BitBlt 失败: {e}")

    # 方法2: PrintWindow
    try:
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        images.append(('PrintWindow', im))
    except Exception as e:
        print(f"    PrintWindow 失败: {e}")

    # 方法3: 屏幕截图
    try:
        im = ImageGrab.grab(bbox=rect)
        images.append(('ScreenGrab', im))
    except Exception as e:
        print(f"    ScreenGrab 失败: {e}")

    return images


def main():
    print("=" * 80)
    print("  截取所有 Androws.exe 窗口")
    print("=" * 80)

    print("\n[1] 查找 Androws.exe 的所有窗口...\n")

    windows = get_all_androws_windows()

    print(f"找到 {len(windows)} 个窗口:\n")

    for i, win in enumerate(windows, 1):
        print(f"窗口 {i}:")
        print(f"  句柄: {win['hwnd']}")
        print(f"  标题: {win['title']}")
        print(f"  类名: {win['class_name']}")
        print(f"  尺寸: {win['width']} x {win['height']}")
        print(f"  可见: {'是' if win['is_visible'] else '否'}")
        print()

    print("=" * 80)
    print("\n[2] 开始截图所有窗口...\n")

    output_dir = 'androws_all_screenshots'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for i, win in enumerate(windows, 1):
        print(f"窗口 {i}: {win['title']} ({win['class_name']}, {win['width']}x{win['height']})")

        if win['width'] <= 0 or win['height'] <= 0:
            print(f"  [跳过] 尺寸无效\n")
            continue

        # 截图
        images = capture_multiple_methods(win['hwnd'], win['rect'])

        if not images:
            print(f"  [失败] 所有截图方法都失败\n")
            continue

        # 保存每种方法的截图
        for method, img in images:
            # 在图片上添加信息
            draw = ImageDraw.Draw(img)
            info_text = f"窗口{i}: {win['title']}\n{win['class_name']}\n{win['width']}x{win['height']}\nHWND:{win['hwnd']}"

            try:
                # 绘制半透明背景
                draw.rectangle([0, 0, 400, 80], fill=(0, 0, 0, 128))
                draw.text((10, 10), info_text, fill='yellow')
            except:
                pass

            # 文件名
            filename = f"window{i:02d}_{method}_{win['class_name']}_{win['width']}x{win['height']}.png"
            filename = "".join(c for c in filename if c.isalnum() or c in '._-')
            filepath = os.path.join(output_dir, filename)

            img.save(filepath)
            print(f"  [OK] {method}: {filename}")

        print()

    print("=" * 80)
    print(f"完成！所有截图已保存到:")
    print(f"  {os.path.abspath(output_dir)}")
    print("=" * 80)

    # 列出所有生成的文件
    files = sorted(os.listdir(output_dir))
    print(f"\n生成的文件 ({len(files)} 个):\n")

    for f in files:
        print(f"  - {f}")

    # 打开目录
    print(f"\n正在打开截图目录...")
    try:
        os.startfile(os.path.abspath(output_dir))
        print("[OK] 已打开")
    except:
        print("[!] 无法自动打开，请手动打开上面的目录")

    print("\n" + "=" * 80)
    print("请逐个查看截图，找到显示斗地主游戏的那个！")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

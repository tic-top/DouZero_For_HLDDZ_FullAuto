"""
高级窗口查找工具 - 使用多种方法找到游戏窗口
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
from PIL import Image, ImageGrab
import psutil
import os


def get_all_windows_including_children():
    """获取所有窗口，包括子窗口"""
    all_windows = []

    def enum_callback(hwnd, results):
        # 不过滤，获取所有窗口
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        is_visible = win32gui.IsWindowVisible(hwnd)

        try:
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
        except:
            width = height = 0

        # 获取进程信息
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()
            exe_path = process.exe()
        except:
            process_name = "Unknown"
            exe_path = ""

        all_windows.append({
            'hwnd': hwnd,
            'title': title,
            'class_name': class_name,
            'is_visible': is_visible,
            'width': width,
            'height': height,
            'process_name': process_name,
            'exe_path': exe_path,
            'rect': rect if width > 0 else None
        })

        return True

    win32gui.EnumWindows(enum_callback, all_windows)
    return all_windows


def capture_window_printwindow(hwnd):
    """使用 PrintWindow API 截取窗口内容（不受遮挡影响）"""
    try:
        # 获取窗口尺寸
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        if width <= 0 or height <= 0:
            return None

        # 创建设备上下文
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        # 创建位图
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        # 使用 PrintWindow 截取窗口
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

        # 转换为 PIL Image
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        # 清理
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return im if result == 1 else None

    except Exception as e:
        return None


def list_game_processes():
    """列出可能的游戏进程"""
    print("\n" + "=" * 80)
    print("当前运行的进程（按CPU使用率排序）:")
    print("=" * 80)

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent']):
        try:
            info = proc.info
            # 过滤系统进程
            if info['name'] and not info['name'].startswith('System'):
                processes.append(info)
        except:
            pass

    # 按CPU使用率排序
    processes.sort(key=lambda p: p.get('cpu_percent', 0), reverse=True)

    print(f"\n{'进程名':<30s} {'PID':<10s} {'CPU%':<10s}")
    print("-" * 80)

    for i, proc in enumerate(processes[:30], 1):  # 只显示前30个
        print(f"{proc['name']:<30s} {proc['pid']:<10d} {proc.get('cpu_percent', 0):<10.1f}")

    print("\n请找到斗地主游戏进程（通常有较高的CPU使用率）")


def find_windows_by_process(process_name):
    """根据进程名查找所有窗口"""
    all_windows = get_all_windows_including_children()

    matching = [w for w in all_windows if process_name.lower() in w['process_name'].lower()]

    return matching


def interactive_find():
    """交互式查找游戏窗口"""
    print("=" * 80)
    print("  交互式游戏窗口查找工具")
    print("=" * 80)

    # 方法1：列出所有进程
    print("\n【方法 1】从进程列表查找")
    list_game_processes()

    print("\n输入游戏进程名（如 Androws.exe）或按 Enter 跳过: ", end='')
    process_name = input().strip()

    if process_name:
        print(f"\n正在查找进程 '{process_name}' 的所有窗口...")
        windows = find_windows_by_process(process_name)

        if windows:
            print(f"\n找到 {len(windows)} 个窗口:")
            print("-" * 80)

            for i, win in enumerate(windows, 1):
                print(f"\n【窗口 {i}】")
                print(f"  句柄 (HWND):   {win['hwnd']}")
                print(f"  标题:          {win['title'] or '(无标题)'}")
                print(f"  类名:          {win['class_name']}")
                print(f"  可见:          {win['is_visible']}")
                print(f"  尺寸:          {win['width']} x {win['height']}")

            # 截取所有窗口
            print("\n正在截取这些窗口...")

            output_dir = 'window_previews_advanced'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            for i, win in enumerate(windows, 1):
                print(f"\n截取窗口 {i} (HWND={win['hwnd']})...")

                # 方法1: PrintWindow
                img = capture_window_printwindow(win['hwnd'])

                if img:
                    filename = f"process_{i:02d}_{win['class_name']}_{win['width']}x{win['height']}.png"
                    filename = "".join(c for c in filename if c.isalnum() or c in '._-')
                    filepath = os.path.join(output_dir, filename)
                    img.save(filepath)
                    print(f"  [OK] 已保存: {filename}")
                else:
                    # 方法2: 屏幕截图
                    if win['rect'] and win['is_visible']:
                        try:
                            img = ImageGrab.grab(bbox=win['rect'])
                            filename = f"screen_{i:02d}_{win['class_name']}_{win['width']}x{win['height']}.png"
                            filename = "".join(c for c in filename if c.isalnum() or c in '._-')
                            filepath = os.path.join(output_dir, filename)
                            img.save(filepath)
                            print(f"  [OK] 已保存 (屏幕截图): {filename}")
                        except:
                            print(f"  [X] 截图失败")
                    else:
                        print(f"  [!] 窗口不可见或无效")

            print(f"\n截图已保存到: {os.path.abspath(output_dir)}")

            # 打开目录
            try:
                os.startfile(os.path.abspath(output_dir))
            except:
                pass

            return

    # 方法2：手动输入窗口句柄
    print("\n" + "=" * 80)
    print("\n【方法 2】手动输入窗口句柄")
    print("\n如果你知道窗口句柄（HWND），可以直接输入")
    print("提示：可以使用 Spy++ 或其他工具查看窗口句柄")

    print("\n输入窗口句柄（十进制数字）或按 Enter 跳过: ", end='')
    hwnd_str = input().strip()

    if hwnd_str.isdigit():
        hwnd = int(hwnd_str)
        print(f"\n正在截取窗口 {hwnd}...")

        img = capture_window_printwindow(hwnd)

        if img:
            output_dir = 'window_previews_advanced'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            filepath = os.path.join(output_dir, f'manual_hwnd_{hwnd}.png')
            img.save(filepath)
            print(f"[OK] 已保存: {filepath}")

            try:
                os.startfile(filepath)
            except:
                pass

            # 获取窗口信息
            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]

                print("\n窗口信息:")
                print(f"  标题: {title}")
                print(f"  类名: {class_name}")
                print(f"  尺寸: {width} x {height}")
            except:
                pass
        else:
            print("[X] 截图失败")

    print("\n完成！")


if __name__ == "__main__":
    try:
        interactive_find()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

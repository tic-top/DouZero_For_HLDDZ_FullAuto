"""
快速截图工具 - 简化版
使用 GameHelper.py 的健壮截图方法
"""
import sys
import os
import io

# 修复编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import win32gui
import win32ui
from ctypes import windll
from PIL import Image, ImageGrab, ImageDraw
from master.utils import get_config


def resolve_handle(window_class=None, window_title=None):
    """
    健壮的窗口查找方法（基于 GameHelper.py）

    Args:
        window_class: 窗口类名
        window_title: 窗口标题

    Returns:
        窗口句柄，未找到返回 None
    """
    # 1. 先按类名查找
    if window_class:
        handle = win32gui.FindWindow(window_class, None)
        if handle:
            print(f"    ✓ 通过类名找到窗口: {window_class}")
            return handle

    # 2. 再按标题查找
    if window_title:
        handle = win32gui.FindWindow(None, window_title)
        if handle:
            print(f"    ✓ 通过标题找到窗口: {window_title}")
            return handle

    # 3. 枚举所有可见窗口，模糊匹配
    candidate_titles = [window_title] if window_title else ["欢乐斗地主"]
    matches = []

    def enum_handler(hwnd, results):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if any(keyword in title for keyword in candidate_titles):
            results.append(hwnd)

    win32gui.EnumWindows(enum_handler, matches)

    if matches:
        print(f"    ✓ 通过枚举找到窗口: {win32gui.GetWindowText(matches[0])}")
        return matches[0]

    print(f"    ✗ 未找到窗口")
    return None


def capture_window(hwnd, method="auto", retries=3):
    """
    使用多重方法截取窗口（基于 GameHelper.py）

    Args:
        hwnd: 窗口句柄
        method: "auto" | "gdi" | "grab"
        retries: 重试次数

    Returns:
        PIL.Image 对象，失败返回 None
    """
    # 设置 DPI 感知，防止坐标缩放
    try:
        windll.user32.SetProcessDPIAware()
    except Exception:
        pass

    def _capture_with_gdi(hwnd, width, height):
        """使用 PrintWindow API 截图（不受遮挡影响）"""
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        # flags: 2=PW_RENDERFULLCONTENT
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        im = Image.frombuffer(
            "RGB",
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        # 清理资源
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        if result != 1:
            raise RuntimeError("PrintWindow 失败或返回黑屏")

        return im

    def _capture_with_grab(rect):
        """使用 ImageGrab 截图（对硬件加速窗口更稳定）"""
        return ImageGrab.grab(bbox=rect)

    # 重试机制
    for attempt in range(retries):
        try:
            # 获取窗口矩形
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                raise RuntimeError("窗口尺寸异常")

            # 尝试截图
            im = None
            last_err = None

            if method in ("auto", "gdi"):
                try:
                    im = _capture_with_gdi(hwnd, width, height)
                    print(f"    ✓ 使用 GDI 方法截图成功")
                except Exception as e:
                    last_err = e
                    if method == "gdi":
                        raise

            if im is None and method in ("auto", "grab"):
                im = _capture_with_grab((left, top, right, bottom))
                print(f"    ✓ 使用 Grab 方法截图成功")

            if im is None:
                raise last_err if last_err else RuntimeError("截图失败")

            return im

        except Exception as e:
            if attempt < retries - 1:
                print(f"    ! 截图失败（尝试 {attempt + 1}/{retries}）: {e}")
                import time
                time.sleep(0.2)
            else:
                print(f"    ✗ 截图失败（已重试 {retries} 次）: {e}")
                raise

    return None


def main():
    print("=" * 60)
    print("快速截图工具")
    print("=" * 60)

    # 加载配置
    config_path = 'config/androws_config.yaml'
    print(f"\n[1] 加载配置: {config_path}")

    config = get_config(config_path)

    window_class = config.get('game.window_class')
    window_title = config.get('game.window_title')

    print(f"    窗口类名: {window_class}")
    print(f"    窗口标题: {window_title}")

    # 查找窗口
    print(f"\n[2] 查找游戏窗口...")

    hwnd = resolve_handle(window_class, window_title)
    if hwnd is None:
        print(f"    [X] 未找到窗口！请先启动游戏")
        return

    rect = win32gui.GetWindowRect(hwnd)
    window_width = rect[2] - rect[0]
    window_height = rect[3] - rect[1]

    print(f"    [OK] 找到窗口: {window_width}x{window_height}")

    # 截图
    print(f"\n[3] 截取游戏窗口...")

    screenshot = capture_window(hwnd, method="auto")
    if screenshot is None:
        print(f"    [X] 截图失败！")
        return

    # 获取截图的实际尺寸
    actual_width, actual_height = screenshot.size
    print(f"    [OK] 截图成功: {actual_width}x{actual_height}")

    # 检查截图尺寸是否与窗口尺寸一致
    if (actual_width, actual_height) != (window_width, window_height):
        print(f"    [!] 警告: 截图尺寸与窗口尺寸不一致")
        print(f"        窗口: {window_width}x{window_height}")
        print(f"        截图: {actual_width}x{actual_height}")

    # 重要：使用截图的实际尺寸来设置分辨率，而不是窗口尺寸
    config.set_resolution(actual_width, actual_height)

    # 绘制检测区域
    print(f"\n[4] 绘制检测区域...")

    draw = ImageDraw.Draw(screenshot)

    # Chat 区域（红色）
    try:
        x, y, w, h = config.get_region('chat_icon')
        draw.rectangle([x, y, x+w, y+h], outline='red', width=2)
        draw.text((x, y-15), 'Chat', fill='red')
        print(f"    Chat 区域: ({x}, {y}, {w}, {h})")
    except:
        print(f"    [!] Chat 区域配置错误")

    # 手牌区域（蓝色）
    try:
        x, y, w, h = config.get_region('my_hand_cards')
        draw.rectangle([x, y, x+w, y+h], outline='blue', width=2)
        draw.text((x, y-15), 'My Cards', fill='blue')
        print(f"    手牌区域: ({x}, {y}, {w}, {h})")
    except:
        print(f"    [!] 手牌区域配置错误")

    # 按钮区域（绿色）
    try:
        x, y, w, h = config.get_region('general_button')
        draw.rectangle([x, y, x+w, y+h], outline='green', width=2)
        draw.text((x, y-15), 'Buttons', fill='green')
        print(f"    按钮区域: ({x}, {y}, {w}, {h})")
    except:
        print(f"    [!] 按钮区域配置错误")

    # 保存截图
    print(f"\n[5] 保存截图...")

    debug_dir = 'debug_screenshots'
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    filepath = os.path.join(debug_dir, 'quick_screenshot.png')
    screenshot.save(filepath)

    abs_path = os.path.abspath(filepath)
    print(f"    [OK] 已保存: {abs_path}")

    # 打开图片
    print(f"\n[6] 打开图片...")
    try:
        os.startfile(abs_path)
        print(f"    [OK] 已打开图片查看器")
    except:
        print(f"    [!] 无法自动打开，请手动查看")

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)

    print("\n请查看截图:")
    print(f"  - 红色框 = Chat 图标区域")
    print(f"  - 蓝色框 = 手牌区域")
    print(f"  - 绿色框 = 按钮区域")

    print(f"\n如果区域位置不对，请修改配置文件:")
    print(f"  {config_path}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

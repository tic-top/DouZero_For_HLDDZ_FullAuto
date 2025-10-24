"""
调试截图工具 - 快速截取游戏窗口并可视化检测区域
"""
import sys
import os
import io

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import win32gui
from PIL import ImageGrab, Image, ImageDraw, ImageFont
import time
from master.utils import get_config


def find_game_window():
    """查找游戏窗口"""
    config = get_config()
    window_class = config.get('game.window_class', 'UnityWndClass')
    window_title = config.get('game.window_title', '欢乐斗地主')

    # 先按类名查找
    hwnd = win32gui.FindWindow(window_class, None)
    if hwnd == 0:
        # 再按标题查找
        hwnd = win32gui.FindWindow(None, window_title)

    if hwnd == 0:
        print(f"❌ 未找到游戏窗口")
        print(f"   查找条件: class='{window_class}', title='{window_title}'")
        return None

    # 获取窗口信息
    rect = win32gui.GetWindowRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]

    print(f"✓ 找到游戏窗口:")
    print(f"  - 句柄: {hwnd}")
    print(f"  - 位置: {rect}")
    print(f"  - 尺寸: {width}x{height}")

    return hwnd


def capture_window(hwnd):
    """截取窗口"""
    rect = win32gui.GetWindowRect(hwnd)
    screenshot = ImageGrab.grab(bbox=rect)

    width = rect[2] - rect[0]
    height = rect[3] - rect[1]

    print(f"\n✓ 截图成功: {width}x{height}")
    return screenshot


def draw_detection_regions(image, config):
    """在截图上绘制所有检测区域"""
    draw = ImageDraw.Draw(image)

    # 获取窗口大小
    width, height = image.size
    config.set_resolution(width, height)

    # 定义要绘制的区域
    regions = {
        'chat_icon': ('Chat 图标', 'red'),
        'my_hand_cards': ('我的手牌', 'blue'),
        'left_played_cards': ('左侧出牌', 'green'),
        'right_played_cards': ('右侧出牌', 'green'),
        'my_played_cards': ('我的出牌', 'cyan'),
        'landlord_cards': ('地主底牌', 'yellow'),
        'pass_button': ('按钮区域', 'orange'),
    }

    print(f"\n绘制检测区域:")
    for region_name, (label, color) in regions.items():
        try:
            x, y, w, h = config.get_region(region_name)

            # 绘制矩形框
            draw.rectangle([x, y, x+w, y+h], outline=color, width=3)

            # 绘制标签
            draw.text((x+5, y+5), f"{label} ({w}x{h})", fill=color)

            print(f"  - {label:15s}: ({x:4d}, {y:4d}, {w:4d}, {h:4d}) [{color}]")

        except Exception as e:
            print(f"  ✗ {region_name}: {e}")

    # 绘制地主标志位置（特殊处理，多个位置）
    landlord_positions = ['右侧玩家', '我', '左侧玩家']
    landlord_flags = config.get('regions.landlord_flags', [])

    if landlord_flags:
        print(f"\n地主标志位置:")
        for i, (pos_name, flag_region) in enumerate(zip(landlord_positions, landlord_flags)):
            x, y, w, h = flag_region
            draw.rectangle([x, y, x+w, y+h], outline='purple', width=2)
            draw.text((x+5, y+5), pos_name, fill='purple')
            print(f"  - {pos_name:10s}: ({x:4d}, {y:4d}, {w:4d}, {h:4d})")

    return image


def save_screenshot(image, filename='debug_game_window.png'):
    """保存截图"""
    debug_dir = os.path.join(os.path.dirname(__file__), 'debug_screenshots')
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)

    filepath = os.path.join(debug_dir, filename)
    image.save(filepath)

    print(f"\n✓ 截图已保存: {filepath}")
    return filepath


def show_screenshot(filepath):
    """显示截图"""
    try:
        import platform
        if platform.system() == 'Windows':
            os.startfile(filepath)
        elif platform.system() == 'Darwin':  # macOS
            os.system(f'open "{filepath}"')
        else:  # Linux
            os.system(f'xdg-open "{filepath}"')

        print(f"✓ 已打开截图查看器")
    except Exception as e:
        print(f"⚠ 无法自动打开图片: {e}")
        print(f"  请手动打开: {filepath}")


def check_templates():
    """检查模板文件是否存在"""
    config = get_config()
    templates_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        config.get('templates.base_path', 'pics')
    )

    print(f"\n模板文件检查:")
    print(f"模板目录: {templates_dir}")

    ui_elements = ['chat', 'chat2', 'laotou', 'continue', 'jiaodizhu_btn',
                   'jiabei_btn', 'start', 'quick_start', 'win', 'lose']

    existing = []
    missing = []

    for element in ui_elements:
        template_path = os.path.join(templates_dir, f"{element}.png")
        if os.path.exists(template_path):
            existing.append(element)
            print(f"  ✓ {element}.png")
        else:
            missing.append(element)
            print(f"  ✗ {element}.png (不存在)")

    print(f"\n统计: {len(existing)}/{len(ui_elements)} 个模板存在")

    if missing:
        print(f"\n缺失的模板: {', '.join(missing)}")

    return existing, missing


def crop_region(image, region, label):
    """裁剪并保存指定区域"""
    x, y, w, h = region
    cropped = image.crop((x, y, x+w, y+h))

    debug_dir = os.path.join(os.path.dirname(__file__), 'debug_screenshots')
    crop_path = os.path.join(debug_dir, f'region_{label}.png')
    cropped.save(crop_path)

    print(f"  → 已保存区域截图: {crop_path}")
    return crop_path


def main():
    """主函数"""
    print("=" * 60)
    print("  游戏窗口调试截图工具")
    print("=" * 60)

    # 加载配置
    config = get_config()

    # 检查模板文件
    check_templates()

    print("\n" + "-" * 60)

    # 查找游戏窗口
    hwnd = find_game_window()
    if hwnd is None:
        print("\n❌ 无法继续，请先启动游戏")
        return

    print("\n" + "-" * 60)

    # 截取窗口
    print("\n正在截取游戏窗口...")
    screenshot = capture_window(hwnd)

    # 保存原始截图
    original_path = save_screenshot(screenshot, 'original_game_window.png')

    # 绘制检测区域
    print("\n" + "-" * 60)
    annotated = draw_detection_regions(screenshot.copy(), config)

    # 保存标注后的截图
    annotated_path = save_screenshot(annotated, 'annotated_game_window.png')

    # 单独保存 chat 区域
    print("\n" + "-" * 60)
    print("\n保存关键区域:")
    width, height = screenshot.size
    config.set_resolution(width, height)

    chat_region = config.get_region('chat_icon')
    crop_region(screenshot, chat_region, 'chat_icon')

    hand_region = config.get_region('my_hand_cards')
    crop_region(screenshot, hand_region, 'my_hand_cards')

    print("\n" + "=" * 60)
    print("✓ 调试截图完成！")
    print("=" * 60)

    print(f"\n生成的文件:")
    print(f"  1. 原始截图: original_game_window.png")
    print(f"  2. 标注截图: annotated_game_window.png")
    print(f"  3. Chat 区域: region_chat_icon.png")
    print(f"  4. 手牌区域: region_my_hand_cards.png")

    print(f"\n所有文件位于: {os.path.join(os.path.dirname(__file__), 'debug_screenshots')}")

    # 询问是否打开
    print("\n" + "-" * 60)
    try:
        response = input("\n是否打开标注截图查看？(y/n): ").strip().lower()
        if response in ['y', 'yes', '']:
            show_screenshot(annotated_path)
    except:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

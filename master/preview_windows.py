"""
窗口预览工具 - 截图所有窗口并保存，帮助找到正确的游戏窗口
"""
import sys
import io

# 修复编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import win32gui
import win32con
from PIL import ImageGrab, ImageDraw, ImageFont
import os


def get_all_windows():
    """获取所有可见窗口"""
    windows = []

    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            # 过滤掉太小的窗口
            if width > 200 and height > 150 and title:
                windows.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class_name': class_name,
                    'rect': rect,
                    'width': width,
                    'height': height
                })
        return True

    win32gui.EnumWindows(callback, windows)

    # 按窗口大小排序（大窗口更可能是游戏）
    windows.sort(key=lambda w: w['width'] * w['height'], reverse=True)

    return windows


def capture_window_screenshot(hwnd, rect):
    """截取窗口截图"""
    try:
        screenshot = ImageGrab.grab(bbox=rect)
        return screenshot
    except Exception as e:
        print(f"    [!] 截图失败: {e}")
        return None


def create_thumbnail(image, max_size=400):
    """创建缩略图"""
    image.thumbnail((max_size, max_size))
    return image


def main():
    print("=" * 80)
    print("  窗口预览工具 - 截图所有窗口帮助找到斗地主")
    print("=" * 80)

    # 创建输出目录
    output_dir = 'window_previews'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"\n[1] 正在获取所有窗口列表...")

    windows = get_all_windows()
    print(f"    找到 {len(windows)} 个可见窗口\n")

    print("[2] 开始截图所有窗口...\n")

    saved_windows = []

    for i, win in enumerate(windows[:15], 1):  # 只处理前15个窗口
        title = win['title']
        class_name = win['class_name']
        width = win['width']
        height = win['height']

        print(f"[{i:2d}] {title[:40]:40s} | {width:4d}x{height:4d}")

        # 截图
        screenshot = capture_window_screenshot(win['hwnd'], win['rect'])

        if screenshot:
            # 在截图上添加标注
            draw = ImageDraw.Draw(screenshot)

            # 绘制窗口信息
            info_text = f"#{i} {title[:30]}"
            try:
                draw.text((10, 10), info_text, fill='red')
            except:
                pass

            # 保存原始截图
            filename = f"window_{i:02d}_{class_name}_{width}x{height}.png"
            # 清理文件名中的非法字符
            filename = "".join(c for c in filename if c.isalnum() or c in '._-')
            filepath = os.path.join(output_dir, filename)

            screenshot.save(filepath)
            print(f"    [OK] 已保存: {filename}")

            saved_windows.append({
                'index': i,
                'title': title,
                'class_name': class_name,
                'width': width,
                'height': height,
                'filepath': filepath
            })
        else:
            print(f"    [!] 截图失败")

        print()

    print("\n" + "=" * 80)
    print(f"完成！共保存 {len(saved_windows)} 个窗口截图")
    print("=" * 80)

    print(f"\n所有截图已保存到: {os.path.abspath(output_dir)}")

    print("\n" + "-" * 80)
    print("接下来的步骤:")
    print("-" * 80)
    print("1. 打开 window_previews/ 目录")
    print("2. 查看每个截图，找到斗地主游戏画面")
    print("3. 记下对应的窗口编号 (如 #5)")
    print("4. 运行此脚本时输入编号查看详细信息")

    # 打开输出目录
    print("\n是否打开 window_previews 目录？(y/n): ", end='')
    try:
        response = input().strip().lower()
        if response in ['y', 'yes', '']:
            os.startfile(os.path.abspath(output_dir))
            print("[OK] 已打开目录")
    except:
        pass

    # 询问用户找到了哪个窗口
    print("\n" + "-" * 80)
    print("找到斗地主游戏窗口了吗？")
    try:
        response = input("输入窗口编号 (如: 5) 或按 Enter 跳过: ").strip()

        if response.isdigit():
            idx = int(response)
            # 找到对应的窗口
            found = None
            for w in saved_windows:
                if w['index'] == idx:
                    found = w
                    break

            if found:
                print("\n" + "=" * 80)
                print(f"窗口 #{found['index']} 详细信息:")
                print("=" * 80)
                print(f"标题 (Title):     {found['title']}")
                print(f"类名 (ClassName): {found['class_name']}")
                print(f"尺寸 (Size):      {found['width']} x {found['height']}")
                print(f"截图文件:         {found['filepath']}")

                print("\n" + "-" * 80)
                print("配置建议 (复制到 config/androws_config.yaml):")
                print("-" * 80)
                print("game:")
                print(f"  window_class: \"{found['class_name']}\"")
                print(f"  window_title: \"{found['title']}\"")
                print(f"  target_resolution:")
                print(f"    width: {found['width']}")
                print(f"    height: {found['height']}")
                print("-" * 80)

                # 询问是否创建配置文件
                print("\n是否自动更新配置文件？(y/n): ", end='')
                update = input().strip().lower()

                if update in ['y', 'yes']:
                    # 读取现有配置
                    config_path = 'config/androws_config.yaml'

                    with open(config_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    # 更新配置
                    new_lines = []
                    in_game_section = False

                    for line in lines:
                        if line.strip().startswith('game:'):
                            in_game_section = True
                            new_lines.append(line)
                        elif in_game_section:
                            if line.startswith('  window_class:'):
                                new_lines.append(f'  window_class: "{found["class_name"]}"\n')
                            elif line.startswith('  window_title:'):
                                new_lines.append(f'  window_title: "{found["title"]}"\n')
                            elif 'width:' in line and 'target_resolution' in ''.join(new_lines[-3:]):
                                new_lines.append(f'    width: {found["width"]}\n')
                            elif 'height:' in line and 'target_resolution' in ''.join(new_lines[-5:]):
                                new_lines.append(f'    height: {found["height"]}\n')
                                in_game_section = False
                            else:
                                new_lines.append(line)
                        else:
                            new_lines.append(line)

                    # 保存配置
                    with open(config_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)

                    print(f"[OK] 配置已更新: {config_path}")

                    print("\n下一步: 运行截图工具验证配置")
                    print("  python quick_screenshot.py")
            else:
                print(f"[!] 未找到编号 {idx} 的窗口")
    except:
        pass

    print("\n完成！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

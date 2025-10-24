"""
列出所有窗口 - 帮助找到正确的游戏窗口
"""
import sys
import io

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import win32gui
import win32con
import win32process
import psutil


def get_window_info(hwnd):
    """获取窗口详细信息"""
    try:
        # 窗口标题
        title = win32gui.GetWindowText(hwnd)

        # 窗口类名
        class_name = win32gui.GetClassName(hwnd)

        # 窗口位置和大小
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        # 是否可见
        is_visible = win32gui.IsWindowVisible(hwnd)

        # 进程信息
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name()
        except:
            process_name = "Unknown"

        return {
            'hwnd': hwnd,
            'title': title,
            'class_name': class_name,
            'rect': rect,
            'width': width,
            'height': height,
            'is_visible': is_visible,
            'process_name': process_name
        }
    except Exception as e:
        return None


def list_all_windows():
    """列出所有窗口"""
    windows = []

    def callback(hwnd, windows):
        info = get_window_info(hwnd)
        if info and info['is_visible'] and info['title']:  # 只显示可见且有标题的窗口
            windows.append(info)
        return True

    win32gui.EnumWindows(callback, windows)
    return windows


def find_doudizhu_windows():
    """查找所有可能的斗地主窗口"""
    all_windows = list_all_windows()

    # 关键词列表
    keywords = ['斗地主', 'doudizhu', 'ddz', '欢乐', 'huanle', 'landlord']

    candidates = []

    for win in all_windows:
        title_lower = win['title'].lower()
        class_lower = win['class_name'].lower()
        process_lower = win['process_name'].lower()

        # 检查是否包含关键词
        for keyword in keywords:
            if (keyword in title_lower or
                keyword in class_lower or
                keyword in process_lower):
                candidates.append(win)
                break

    return candidates


def main():
    """主函数"""
    print("=" * 80)
    print("  Windows 窗口列表工具 - 查找斗地主游戏窗口")
    print("=" * 80)

    # 查找斗地主相关窗口
    print("\n[*] 正在查找斗地主相关窗口...\n")
    doudizhu_windows = find_doudizhu_windows()

    if doudizhu_windows:
        print(f"[OK] 找到 {len(doudizhu_windows)} 个可能的斗地主窗口:\n")

        for i, win in enumerate(doudizhu_windows, 1):
            print(f"【窗口 {i}】")
            print(f"  标题 (Title):     {win['title']}")
            print(f"  类名 (ClassName): {win['class_name']}")
            print(f"  进程 (Process):   {win['process_name']}")
            print(f"  句柄 (HWND):      {win['hwnd']}")
            print(f"  尺寸 (Size):      {win['width']} x {win['height']}")
            print(f"  位置 (Rect):      {win['rect']}")
            print()

        print("-" * 80)
        print("\n[提示] 使用建议:")
        print("\n如果上面的窗口是正确的斗地主窗口，请更新配置文件:")
        print("编辑 master/config/default.yaml，修改以下内容:\n")

        # 推荐第一个窗口的配置
        best = doudizhu_windows[0]
        print("game:")
        print(f"  window_class: \"{best['class_name']}\"")
        print(f"  window_title: \"{best['title']}\"")
        print(f"  target_resolution:")
        print(f"    width: {best['width']}")
        print(f"    height: {best['height']}")

    else:
        print("[!] 未找到斗地主相关窗口")
        print("\n可能的原因:")
        print("  1. 游戏未启动")
        print("  2. 游戏窗口标题不包含'斗地主'等关键词")
        print("\n显示所有可见窗口（包含大小信息）:\n")

        all_windows = list_all_windows()

        # 过滤掉太小的窗口（可能不是主窗口）
        main_windows = [w for w in all_windows if w['width'] > 400 and w['height'] > 300]

        # 按窗口大小排序（大窗口更可能是游戏窗口）
        main_windows.sort(key=lambda w: w['width'] * w['height'], reverse=True)

        print(f"找到 {len(main_windows)} 个主要窗口（宽高 > 400x300）:\n")

        for i, win in enumerate(main_windows[:20], 1):  # 只显示前20个
            print(f"【{i:2d}】 {win['title'][:50]:50s} | {win['class_name'][:20]:20s} | {win['width']:4d}x{win['height']:4d} | {win['process_name']}")

        if len(main_windows) > 20:
            print(f"\n... 还有 {len(main_windows) - 20} 个窗口未显示")

        print("\n" + "-" * 80)
        print("\n[提示]:")
        print("  1. 启动斗地主游戏")
        print("  2. 从上面的列表中找到游戏窗口")
        print("  3. 记录对应的 ClassName 和 Title")
        print("  4. 更新 master/config/default.yaml 配置文件")

    print("\n" + "=" * 80)

    # 提供交互式查询
    print("\n是否要查看某个窗口的详细信息？")
    try:
        response = input("输入窗口编号 (或按 Enter 跳过): ").strip()
        if response.isdigit():
            idx = int(response) - 1
            windows_list = doudizhu_windows if doudizhu_windows else main_windows
            if 0 <= idx < len(windows_list):
                win = windows_list[idx]
                print("\n详细信息:")
                print(f"  窗口句柄 (HWND):  {win['hwnd']}")
                print(f"  标题 (Title):     {win['title']}")
                print(f"  类名 (ClassName): {win['class_name']}")
                print(f"  进程名 (Process): {win['process_name']}")
                print(f"  窗口位置 (Rect):  {win['rect']}")
                print(f"  窗口尺寸 (Size):  {win['width']} x {win['height']}")
                print(f"  是否可见:         {win['is_visible']}")

                # 提供配置
                print("\n配置建议:")
                print("---")
                print("game:")
                print(f"  window_class: \"{win['class_name']}\"")
                print(f"  window_title: \"{win['title']}\"")
                print(f"  target_resolution:")
                print(f"    width: {win['width']}")
                print(f"    height: {win['height']}")
                print("---")
    except:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()

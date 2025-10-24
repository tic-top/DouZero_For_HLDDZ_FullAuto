"""
DouZero Agent - 主入口

一个更加模块化、灵活、可扩展的斗地主 AI Agent
使用 GameHelper.py 的健壮截图方法
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from master.utils import get_config
from master.core import GameState, GamePhase, PlayerPosition
from master.agents import DouZeroAgent
from master.detection import CardDetector, TemplateDetector
from master.actions import MouseExecutor, CardSelector, BidExecutor


# ============================================================================
# 辅助函数：健壮的窗口查找和截图（基于 GameHelper.py）
# ============================================================================

def resolve_handle(window_class=None, window_title=None):
    """
    健壮的窗口查找方法

    Args:
        window_class: 窗口类名
        window_title: 窗口标题

    Returns:
        窗口句柄，未找到返回 None
    """
    import win32gui

    # 1. 先按类名查找
    if window_class:
        handle = win32gui.FindWindow(window_class, None)
        if handle:
            print(f"✓ 通过类名找到窗口: {window_class}")
            return handle

    # 2. 再按标题查找
    if window_title:
        handle = win32gui.FindWindow(None, window_title)
        if handle:
            print(f"✓ 通过标题找到窗口: {window_title}")
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
        print(f"✓ 通过枚举找到窗口: {win32gui.GetWindowText(matches[0])}")
        return matches[0]

    return None


def capture_window(hwnd, method="auto", retries=3):
    """
    使用多重方法截取窗口

    Args:
        hwnd: 窗口句柄
        method: "auto" | "gdi" | "grab"
        retries: 重试次数

    Returns:
        PIL.Image 对象，失败返回 None
    """
    import win32gui
    import win32ui
    from ctypes import windll
    from PIL import Image, ImageGrab

    # 设置 DPI 感知
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
        """使用 ImageGrab 截图"""
        return ImageGrab.grab(bbox=rect)

    # 重试机制
    for attempt in range(retries):
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                raise RuntimeError("窗口尺寸异常")

            im = None
            last_err = None

            # 尝试 GDI 方法
            if method in ("auto", "gdi"):
                try:
                    im = _capture_with_gdi(hwnd, width, height)
                except Exception as e:
                    last_err = e
                    if method == "gdi":
                        raise

            # 回退到 Grab 方法
            if im is None and method in ("auto", "grab"):
                im = _capture_with_grab((left, top, right, bottom))

            if im is None:
                raise last_err if last_err else RuntimeError("截图失败")

            return im

        except Exception as e:
            if attempt < retries - 1:
                import time
                time.sleep(0.2)
            else:
                raise

    return None


class DouZeroGameAgent:
    """
    DouZero 游戏 Agent - 主控制器

    整合所有模块，实现完整的游戏自动化流程
    """

    def __init__(self, config_path: str = None):
        """
        初始化 Agent

        Args:
            config_path: 配置文件路径（可选）
        """
        # 加载配置
        self.config = get_config(config_path)
        print(f"配置已加载: {self.config.config_path}")

        # 初始化游戏状态
        self.state = GameState()

        # 初始化检测器
        self.card_detector = CardDetector(self.config)
        self.ui_detector = TemplateDetector(self.config)
        self._load_ui_templates()

        # 初始化动作执行器
        self.mouse = MouseExecutor(self.config)
        self.card_selector = CardSelector(self.config, self.mouse)
        self.bid_executor = BidExecutor(self.config, self.mouse)

        # AI Agent（延迟初始化，等确定位置后）
        self.ai_agent = None

        # 游戏窗口句柄
        self.window_handle = None

        print("DouZero Agent 初始化完成")

    def _load_ui_templates(self):
        """加载 UI 模板"""
        import os

        templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            self.config.get('templates.base_path', 'pics')
        )

        # 加载常用的 UI 元素模板
        ui_elements = [
            'chat', 'chat2',           # 聊天图标
            'laotou',                   # 地主标志
            'continue',                 # 继续按钮
            'jiaodizhu_btn',           # 叫地主按钮
            'jiabei_btn',              # 加倍按钮
            'start', 'quick_start',    # 开始按钮
            'win', 'lose',             # 胜利/失败
        ]

        loaded_count = 0
        for element in ui_elements:
            template_path = os.path.join(templates_dir, f"{element}.png")
            if os.path.exists(template_path):
                self.ui_detector.load_template(element, template_path)
                loaded_count += 1
                print(f"✓ 已加载模板: {element}")
            else:
                print(f"✗ 模板不存在: {template_path}")

        print(f"\n总计加载 {loaded_count}/{len(ui_elements)} 个 UI 模板")

    def _update_resolution_from_screenshot(self, screenshot) -> bool:
        """
        根据截图更新分辨率配置

        Args:
            screenshot: PIL.Image 对象

        Returns:
            是否成功更新
        """
        if screenshot is None:
            return False

        actual_width, actual_height = screenshot.size
        self.config.set_resolution(actual_width, actual_height)
        return True

    def find_game_window(self) -> bool:
        """
        查找游戏窗口（使用健壮的查找方法）

        Returns:
            是否找到窗口
        """
        import win32gui

        window_class = self.config.get('game.window_class', 'UnityWndClass')
        window_title = self.config.get('game.window_title', '欢乐斗地主')

        print(f"正在查找游戏窗口...")
        print(f"  类名: {window_class}")
        print(f"  标题: {window_title}")

        try:
            # 使用健壮的窗口查找方法
            hwnd = resolve_handle(window_class, window_title)

            if hwnd is None:
                print(f"✗ 未找到游戏窗口")
                return False

            self.window_handle = hwnd
            self.mouse.set_window_handle(hwnd)

            # 获取窗口大小
            rect = win32gui.GetWindowRect(hwnd)
            window_width = rect[2] - rect[0]
            window_height = rect[3] - rect[1]

            # 进行一次测试截图以获取实际尺寸
            test_screenshot = capture_window(hwnd, method="auto")
            if test_screenshot:
                actual_width, actual_height = test_screenshot.size

                # 使用截图的实际尺寸来设置分辨率（更准确）
                self._update_resolution_from_screenshot(test_screenshot)

                if (actual_width, actual_height) != (window_width, window_height):
                    print(f"  注意: 截图尺寸({actual_width}x{actual_height}) != 窗口尺寸({window_width}x{window_height})")

                print(f"✓ 窗口信息: hwnd={hwnd}, 窗口={window_width}x{window_height}, 截图={actual_width}x{actual_height}")
            else:
                # 截图失败，使用窗口尺寸（备用方案）
                self.config.set_resolution(window_width, window_height)
                print(f"⚠ 测试截图失败，使用窗口尺寸: {window_width}x{window_height}")
                print(f"✓ 窗口信息: hwnd={hwnd}")

            return True

        except Exception as e:
            print(f"✗ 查找窗口失败: {e}")
            return False

    def wait_for_game_start(self, debug=True) -> bool:
        """
        等待游戏开始（使用健壮的截图方法）

        Args:
            debug: 是否保存调试截图

        Returns:
            是否成功进入游戏
        """
        from PIL import ImageDraw
        import os

        self.state.transition_to(GamePhase.WAITING_START)

        print("\n等待进入游戏...")

        # 创建调试目录
        debug_dir = os.path.join(os.path.dirname(__file__), 'debug_screenshots')
        if debug and not os.path.exists(debug_dir):
            os.makedirs(debug_dir)

        max_attempts = 60  # 最多等待 60 秒
        for i in range(max_attempts):
            try:
                # 使用健壮的截图方法
                screenshot = capture_window(self.window_handle, method="auto")

                if screenshot is None:
                    print(f"\n[警告] 截图失败（尝试 {i+1}/{max_attempts}）")
                    import time
                    time.sleep(1)
                    continue

                # 重要：每次截图后，根据实际尺寸重新设置分辨率
                self._update_resolution_from_screenshot(screenshot)

                # 根据当前分辨率获取聊天图标区域
                chat_region = self.config.get_region('chat_icon')

                # 首次输出检测区域信息
                if i == 0:
                    actual_width, actual_height = screenshot.size
                    print(f"截图尺寸: {actual_width}x{actual_height}")
                    print(f"检测区域: {chat_region}")

                # 保存调试截图（每5秒保存一次）
                if debug and i % 5 == 0:
                    debug_path = os.path.join(debug_dir, f'waiting_game_{i}.png')

                    # 在截图上标记检测区域
                    debug_img = screenshot.copy()
                    draw = ImageDraw.Draw(debug_img)
                    x, y, w, h = chat_region
                    draw.rectangle([x, y, x+w, y+h], outline='red', width=3)
                    draw.text((x, y-20), f'Chat Region (attempt {i})', fill='red')

                    debug_img.save(debug_path)
                    print(f"\n[调试] 已保存截图: {debug_path}")

                # 检测聊天图标
                chat_pos = self.ui_detector.detect(screenshot, 'chat', region=chat_region)
                if chat_pos is None:
                    chat_pos = self.ui_detector.detect(screenshot, 'chat2', region=chat_region)

                if chat_pos:
                    print(f"\n✓ 已进入游戏！检测到 chat 图标位置: {chat_pos}")

                    # 保存成功检测的截图
                    if debug:
                        success_path = os.path.join(debug_dir, 'game_started_success.png')
                        debug_img = screenshot.copy()
                        draw = ImageDraw.Draw(debug_img)
                        draw.rectangle([chat_pos[0], chat_pos[1],
                                      chat_pos[0]+50, chat_pos[1]+50],
                                      outline='green', width=3)
                        draw.text(chat_pos, 'Chat Found!', fill='green')
                        debug_img.save(success_path)
                        print(f"[调试] 成功截图已保存: {success_path}")

                    self.state.transition_to(GamePhase.BIDDING)
                    return True

                print(".", end="", flush=True)

            except Exception as e:
                print(f"\n[错误] 检测过程出错: {e}")

            import time
            time.sleep(1)

        print("\n✗ 等待超时 - 未检测到游戏窗口")

        # 保存最终失败的截图
        if debug:
            try:
                screenshot = capture_window(self.window_handle, method="auto")
                if screenshot:
                    fail_path = os.path.join(debug_dir, 'game_start_failed.png')
                    debug_img = screenshot.copy()
                    draw = ImageDraw.Draw(debug_img)
                    x, y, w, h = chat_region
                    draw.rectangle([x, y, x+w, y+h], outline='red', width=3)
                    draw.text((x, y-20), 'Chat NOT Found', fill='red')
                    debug_img.save(fail_path)
                    print(f"[调试] 失败截图已保存: {fail_path}")
            except Exception as e:
                print(f"[调试] 无法保存失败截图: {e}")

            print(f"[调试] 所有截图保存在: {debug_dir}")

        return False

    def initialize_agent(self, position: PlayerPosition):
        """
        初始化 AI Agent

        Args:
            position: 玩家位置
        """
        if self.ai_agent is None:
            position_str = position.value
            self.ai_agent = DouZeroAgent(self.config, position_str)
            self.state.set_my_position(position)
            print(f"AI Agent 已初始化: {position.name}")

    def run(self):
        """运行主循环"""
        print("=" * 50)
        print("DouZero Agent 启动")
        print("=" * 50)

        # 查找游戏窗口
        if not self.find_game_window():
            print("错误: 未找到游戏窗口，请先启动游戏")
            return

        # 等待游戏开始
        if not self.wait_for_game_start():
            print("错误: 未能进入游戏")
            return

        print("\n游戏流程开始...")
        print("提示: 这是一个演示框架，实际游戏逻辑需要进一步实现")

        # TODO: 实现完整的游戏循环
        # 1. 叫地主阶段
        # 2. 加倍阶段
        # 3. 出牌阶段
        # 4. 游戏结束处理

    def cleanup(self):
        """清理资源"""
        self.state.reset()
        print("资源已清理")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='DouZero Game Agent')
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='配置文件路径'
    )
    parser.add_argument(
        '--position',
        type=str,
        choices=['landlord', 'landlord_up', 'landlord_down'],
        default='landlord',
        help='玩家位置'
    )

    args = parser.parse_args()

    # 创建 Agent
    agent = DouZeroGameAgent(args.config)

    # 初始化 AI
    position_map = {
        'landlord': PlayerPosition.LANDLORD,
        'landlord_up': PlayerPosition.LANDLORD_UP,
        'landlord_down': PlayerPosition.LANDLORD_DOWN,
    }
    agent.initialize_agent(position_map[args.position])

    try:
        # 运行
        agent.run()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()

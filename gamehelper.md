  GameHelper 的作用

  核心定位：Windows 游戏自动化工具包

  ┌─────────────────────────────────────┐
  │         mian.py (业务逻辑)           │
  │   - 游戏状态判断                      │
  │   - AI 决策                          │
  │   - 出牌逻辑                          │
  └─────────────┬───────────────────────┘
                │ 调用
  ┌─────────────▼───────────────────────┐
  │       GameHelper (工具层)            │
  │   提供底层能力：                      │
  │   1. 截取游戏画面                     │
  │   2. 识别游戏元素                     │
  │   3. 控制鼠标点击                     │
  │   4. 管理模板图片                     │
  └─────────────┬───────────────────────┘
                │ 使用
  ┌─────────────▼───────────────────────┐
  │       Windows API                    │
  │   - win32gui (窗口操作)              │
  │   - win32ui (设备上下文)              │
  │   - OpenCV (图像识别)                │
  └─────────────────────────────────────┘

  主要功能模块

  1. 窗口管理

  # 查找游戏窗口
  self.Handle = win32gui.FindWindow("UnityWndClass", None)

  # 调整窗口大小
  win32gui.MoveWindow(hwnd, left, top, 1440, 810, True)

  # 获取窗口位置
  left, top, right, bot = win32gui.GetWindowRect(hwnd)

  作用：
  - 🔍 找到游戏窗口：通过类名或标题定位
  - 📏 统一窗口大小：强制调整为 1440x810，保证坐标准确
  - 📍 获取窗口位置：用于坐标转换

  ---
  2. 截图能力 🎯 最核心功能

  def Screenshot(self, region=None):
      # 1. 找到窗口
      hwnd = win32gui.FindWindow(None, "腾讯欢乐斗地主")

      # 2. 使用 PrintWindow 截取（可以截后台窗口！）
      windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

      # 3. 返回 PIL Image 对象
      return im, (left, top)

  作用：
  - 📸 后台截图：不需要窗口在前台，可以边玩边截
  - 🎯 区域截图：可以只截取指定区域（如手牌区、按钮区）
  - 🔄 失败重试：最多重试 3 次，提高稳定性

  ---
  3. 图像识别

  # 加载所有模板图片到内存
  for file in os.listdir("./pics"):
      tmpImage = Image.open("./pics/" + file)
      imgCv = cv2.imread("./pics/" + file)
      self.Pics.update({info[0]: tmpImage})      # PIL 格式
      self.PicsCV.update({info[0]: imgCv})       # OpenCV 格式

  # 在屏幕上查找图片
  def LocateOnScreen(self, templateName, region, confidence=0.8):
      # 使用 OpenCV 模板匹配
      result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
      return (x, y)  # 返回找到的坐标

  作用：
  - 🖼️ 模板匹配：识别按钮、牌型、弹窗等
  - 📦 预加载优化：启动时加载所有模板，避免重复 I/O
  - 🎚️ 置信度控制：可调整识别精度（0-1）

  识别的内容示例：
  ./pics/
  ├── jiaodizhu_btn.png    # 叫地主按钮
  ├── jiabei_btn.png       # 加倍按钮
  ├── pass_btn.png         # 要不起按钮
  ├── play_card.png        # 出牌按钮
  ├── chat.png             # 聊天按钮（用于判断在游戏内）
  ├── laotou.png           # 底牌（用于判断游戏开始）
  ├── m3.png, m4.png...    # 手牌（3、4、5等）
  └── ...

  ---
  4. 鼠标控制

  def LeftClick(self, pos):
      # 1. 坐标转换（从 1440x810 基准转换到实际窗口）
      x = int((pos[0] / 1440) * self.RealRate[0])
      y = int((pos[1] / 810) * self.RealRate[1])

      # 2. 转换为屏幕坐标
      left, top, _, _ = win32gui.GetWindowRect(self.Handle)
      m, n = int(left + x), int(top + y)

      # 3. 发送点击消息（不依赖真实鼠标移动！）
      win32gui.SendMessage(self.Handle, win32con.WM_LBUTTONDOWN, ...)
      win32gui.SendMessage(self.Handle, win32con.WM_LBUTTONUP, ...)

      # 4. 把鼠标移开（避免影响下次识别）
      win32api.SetCursorPos((int(left + 1000), int(top + 550)))

  作用：
  - 🖱️ 精确点击：像素级精度
  - 🎯 后台操作：通过 SendMessage 可以点击后台窗口
  - 🔄 自动缩放：自动处理不同窗口大小的坐标转换
  - 🧹 清理鼠标：点击后移开，不影响下次截图识别

  两种点击方式：
  - LeftClick(pos)：点击后等待 200ms 并移开鼠标
  - LeftClick2(pos)：快速点击，不等待（用于选牌）

  ---
  5. 组合功能

  def ClickOnImage(self, templateName, region=None, confidence=0.8):
      # 1. 截图
      image, _ = self.Screenshot()

      # 2. 在截图中找到目标
      result = LocateOnImage(image, self.PicsCV[templateName], region)

      # 3. 如果找到，点击它
      if result is not None:
          self.LeftClick(result)

  作用：
  - 🎯 一键操作："找到XXX按钮并点击"
  - 🔍 自动定位：不需要硬编码坐标
  - ⚠️ 容错处理：找不到就不点，不会崩溃

  使用场景：
  # 点击"继续"按钮
  helper.ClickOnImage("continue", region=(1100, 617, 200, 74))

  # 点击"快速开始"
  helper.ClickOnImage("quick_start", region=(1107, 679, 252, 118))

  # 点击"出牌"按钮
  helper.ClickOnImage("play_card", region=(200, 450, 1000, 120))

  ---
  6. 辅助工具

  # 延时（不阻塞 Qt 事件循环）
  def sleep(self, ms):
      self.counter.restart()
      while self.counter.elapsed() < ms:
          QtWidgets.QApplication.processEvents(QEventLoop.AllEvents, 50)

  # 鼠标滚轮
  @staticmethod
  def MouseScroll(amount):
      win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, amount, 0)

  # 鼠标移动（带动画效果）
  def MoveTo(self, pos):
      pyautogui.moveTo(x, y)

  ---
  在 mian.py 中的使用示例

  # 全局创建实例
  helper = GameHelper()

  # 1. 检测游戏状态
  result = helper.LocateOnScreen("chat", region=(1302, 744, 117, 56))
  if result is not None:
      print("在游戏场内")

  # 2. 识别手牌
  img, _ = helper.Screenshot()
  my_cards = self.find_my_cards()  # 内部使用 helper.Screenshot()

  # 3. 点击按钮
  helper.ClickOnImage("jiaodizhu_btn", region=self.GeneralBtnPos)

  # 4. 选牌并出牌
  self.click_cards("AAAKK")  # 内部使用 helper.LeftClick2()
  helper.ClickOnImage("play_card", region=self.PassBtnPos)

  总结：GameHelper 就像一个"机器人的手和眼"

  | 功能             | 类比      | 实际作用    |
  |----------------|---------|---------|
  | Screenshot     | 👀 眼睛   | 看到游戏画面  |
  | LocateOnScreen | 🧠 视觉识别 | 识别按钮、牌型 |
  | LeftClick      | 🖱️ 手   | 点击按钮、选牌 |
  | ClickOnImage   | 🤖 自动化  | "看到就点"  |
  | 模板库            | 📚 记忆   | 记住各种图案  |

  核心优势：
  ✅ 后台运行（PrintWindow）✅ 精确控制（SendMessage）✅ 高性能（预加载模板）✅ 易维护（图片 + 区域参数）
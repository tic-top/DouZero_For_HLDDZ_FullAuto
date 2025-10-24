# -*- coding: utf-8 -*-
# @Time : 2024/2/14 17:06
# @Author : MaYun
# @File : GameHelper.py
# @Software: PyCharm
import ctypes
import json
import win32gui
import win32ui
import win32api
import win32con
from ctypes import windll
from PIL import Image
import cv2
import pyautogui
import matplotlib.pyplot as plt
import numpy as np
import os
import time
from PyQt5  import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QTime, QEventLoop
from skimage.metrics import structural_similarity as ssim

Pics = {}
def read_json():
    with open('data.json', 'r') as f:
        content = f.read()
        data = json.loads(content)
        f.close()
    return data
def write_json(data):
    with open('data.json', 'w') as f:
        json.dump(data, f)
        f.close()
def compare_images(image1, image2):
    img2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
    # 转换为灰度图
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)    # 使用结构相似性指数（SSIM）比较相似度
    ssim_index, _ = ssim(gray1, gray2, full=True)
    return ssim_index
def ShowImg(image):
    plt.imshow(image)
    plt.show()
def DrawRectWithText(image, rect, text):
    img = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    x, y, w, h = rect
    img2 = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
    img2 = cv2.putText(img2, text, (x, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    return Image.fromarray(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
def CompareCard(card):
    order = {"3": 0, "4": 1, "5": 2, "6": 3, "7": 4, "8": 5, "9": 6, "T": 7, "J": 8, "Q": 9, "K": 10, "A": 11, "2": 12,
             "X": 13, "D": 14}
    return order[card]
def CompareCardInfo(card):
    order = {"3": 0, "4": 1, "5": 2, "6": 3, "7": 4, "8": 5, "9": 6, "T": 7, "J": 8, "Q": 9, "K": 10, "A": 11, "2": 12,
             "X": 13, "D": 14}
    return order[card[0]]
def CompareCards(cards1, cards2):
    if len(cards1) != len(cards2):
        return False
    cards1.sort(key=CompareCard)
    cards2.sort(key=CompareCard)
    for i in range(0, len(cards1)):
        if cards1[i] != cards2[i]:
            return False
    return True
def GetListDifference(l1, l2):
    temp1 = []
    temp1.extend(l1)
    temp2 = []
    temp2.extend(l2)
    for i in l2:
        if i in temp1:
            temp1.remove(i)
    for i in l1:
        if i in temp2:
            temp2.remove(i)
    return temp1, temp2
def FindImage(fromImage, template, threshold=0.9):
    w, h, _ = template.shape
    fromImage = cv2.cvtColor(np.asarray(fromImage), cv2.COLOR_RGB2BGR)
    res = cv2.matchTemplate(fromImage, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    points = []
    for pt in zip(*loc[::-1]):
        points.append(pt)
    return points
def LocateOnImage(image, template, region=None, confidence=0.8):
    if region is not None:
        x, y, w, h = region
        imgShape = image.shape
        image = image[y:y + h, x:x + w, :]
    res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, _, _, maxLoc = cv2.minMaxLoc(res)
    if (res >= confidence).any():
        return region[0] + maxLoc[0], region[1] + maxLoc[1]
    else:
        return None
def LocateAllOnImage(image, template, region=None, confidence=0.8):
    if region is not None:
        x, y, w, h = region
        image = image[y:y + h, x:x + w]
    w, h = image.shape[1], image.shape[0]    
    res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= confidence)
    points = []
    for pt in zip(*loc[::-1]):
        points.append((pt[0], pt[1], w, h))
    return points

class GameHelper:
    def __init__(self):
        self.ScreenZoomRate = None
        self.counter = QTime()
        self.Pics = {}
        self.PicsCV = {}
        st = time.time()
        self.Handle = self.resolve_handle()
        self.Interrupt = False
        self.RealRate = (1440, 810)
        self.GetZoomRate()
        for file in os.listdir("./pics"):
            info = file.split(".")
            if info[1] == "png":
                tmpImage = Image.open("./pics/" + file)
                imgCv = cv2.imread("./pics/" + file)
                self.Pics.update({info[0]: tmpImage})
                self.PicsCV.update({info[0]: imgCv})    
    
    def resolve_handle(self):
        """Locate the 游戏窗口 handle by class name or known window titles."""
        handle = win32gui.FindWindow("UnityWndClass", None)
        if handle:
            print("Found window by class name: Unity")
            return handle
        candidate_titles = [
            "欢乐斗地主"
        ]
        matches = []        
        
        def enum_handler(hwnd, results):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if any(keyword in title for keyword in candidate_titles):
                results.append(hwnd)
        win32gui.EnumWindows(enum_handler, matches)
        if not matches:
            print("Warning: Could not find 欢乐斗地主 window. Capturing the entire screen instead.")

        return matches[0] if matches else None

    def sleep(self, ms):
        self.counter.restart()
        while self.counter.elapsed() < ms:
            QtWidgets.QApplication.processEvents(QEventLoop.AllEvents, 50)

    def Screenshot(self, region=None, target_size=(1440, 810), crop_after_resize=True, method="auto", retries=3):
        """
        截图指定窗口。
        - region: (x, y, w, h)。如果 crop_after_resize=True，则基于缩放后的图像坐标裁剪；
                否则基于原始窗口坐标裁剪。
        - target_size: 缩放后的目标分辨率，例如 (1440, 810)。传 None 则不缩放。
        - crop_after_resize: 是否在缩放后再裁剪（更直观，推荐）。
        - method: "auto" | "gdi" | "grab"。auto 先 GDI 再回退抓屏。
        - retries: 重试次数。
        返回: (PIL.Image, (left, top))；失败则 (None, (0, 0))
        """
        import ctypes
        from ctypes import windll
        import win32gui
        import win32ui
        from PIL import Image, ImageGrab

        # 确保 DPI 感知，防止坐标缩放导致的偏移/模糊
        try:
            windll.user32.SetProcessDPIAware()
        except Exception:
            pass

        def _capture_with_gdi(hwnd, width, height):
            # 使用 PrintWindow 拍全内容（含非客户区）。某些窗口会返回黑屏，失败时回退到 ImageGrab
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            # flags: 2=PW_RENDERFULLCONTENT；1=PW_CLIENTONLY；这里用 2，必要时你也可试 0 或 1
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
            if result != 1:
                # 某些情况下 PrintWindow 返回 0/黑图
                raise RuntimeError("PrintWindow failed or produced incomplete image.")
            return im

        def _capture_with_grab(rect):
            # 直接从屏幕抓取 bbox（对部分硬件加速窗口更稳定）
            return ImageGrab.grab(bbox=rect)

        try_count = retries
        while try_count > 0:
            try:
                try_count -= 1

                # 1) 定位窗口
                self.Handle = self.resolve_handle()
                if not self.Handle:
                    raise RuntimeError("未找到目标窗口（请先打开游戏/窗口）。")

                hwnd = self.Handle

                # 2) 读取窗口矩形，不改变窗口大小
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                win_w, win_h = right - left, bottom - top
                if win_w <= 0 or win_h <= 0:
                    raise RuntimeError("窗口尺寸异常。")

                self.RealRate = (win_w, win_h)  # 记录实际窗口分辨率（未缩放）
                origin = (left, top)

                # 3) 截图（优先 GDI，失败回退抓屏）
                im = None
                last_err = None

                if method in ("auto", "gdi"):
                    try:
                        im = _capture_with_gdi(hwnd, win_w, win_h)
                    except Exception as e:
                        last_err = e

                if im is None and method in ("auto", "grab"):
                    # 注意：ImageGrab 抓到的是“屏幕像素”，在有透明/置顶窗口时可能被遮挡
                    im = _capture_with_grab((left, top, right, bottom))

                if im is None:
                    # 两种方式都失败
                    raise last_err if last_err else RuntimeError("无法截图。")

                # 4) 裁剪/缩放
                if region and not crop_after_resize:
                    # 先裁剪（以原始窗口坐标）
                    x, y, w, h = region
                    im = im.crop((x, y, x + w, y + h))

                if target_size:
                    im = im.resize(target_size)

                if region and crop_after_resize:
                    # 在缩放后裁剪：region 应以 target_size 的坐标为准
                    x, y, w, h = region
                    im = im.crop((x, y, x + w, y + h))

                return im, origin

            except Exception as e:
                print("截图时出现错误:", repr(e))
                # 小憩一下再试（如果你有自带 sleep）
                try:
                    self.sleep(200)
                except Exception:
                    pass

        return None, (0, 0)
    
    def GetZoomRate(self):
        self.ScreenZoomRate = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100    
    
    def LocateOnScreen(self, templateName, region, confidence=0.8, img=None):
        if img is not None:
            image = img
        else:
            image, _ = self.Screenshot()
        imgcv = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        return LocateOnImage(imgcv, self.PicsCV[templateName], region=region, confidence=confidence)    
    
    def ClickOnImage(self, templateName, region=None, confidence=0.8, img=None):
        if img is not None:
            image = img
        else:
            image, _ = self.Screenshot()
        imgcv = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
        result = LocateOnImage(imgcv, self.PicsCV[templateName], region=region, confidence=confidence)        
        if result is not None:
            self.LeftClick(result)
            # print(result)    
    
    def LeftClick(self, pos):
        x = int((pos[0] / 1440) * self.RealRate[0])
        y = int((pos[1] / 810) * self.RealRate[1])        
        left, top, _, _ = win32gui.GetWindowRect(self.Handle)
        m, n = int(left + x), int(top + y)
        client_pos = (x, y)
        win32api.SetCursorPos((m, n))
        tmp = win32api.MAKELONG(client_pos[0], client_pos[1])        
        win32gui.PostMessage(self.Handle, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        win32gui.SendMessage(self.Handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, tmp)
        win32gui.SendMessage(self.Handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, tmp)
        self.sleep(200)
        win32api.SetCursorPos((int(left + 1000), int(top + 550)))    
        
    def LeftClick2(self, pos):
        x = int((pos[0] / 1440) * self.RealRate[0])
        y = int((pos[1] / 810) * self.RealRate[1])        
        left, top, _, _ = win32gui.GetWindowRect(self.Handle)
        m, n = int(left + x), int(top + y)
        client_pos = (x, y)        
        win32api.SetCursorPos((m, n))
        tmp = win32api.MAKELONG(client_pos[0], client_pos[1])
        win32gui.PostMessage(self.Handle, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        win32gui.SendMessage(self.Handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, tmp)
        win32gui.SendMessage(self.Handle, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, tmp)    
    
    def MoveTo(self, pos):
        x = int((pos[0] / 1440) * self.RealRate[0])
        y = int((pos[1] / 810) * self.RealRate[1])
        left, top, _, _ = win32gui.GetWindowRect(self.Handle)
        x, y = int(left + x), int(top + y)
        pyautogui.moveTo(x, y)    
    
    @staticmethod
    def MouseScroll(amount):
        # 发送鼠标滚轮事件
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, amount, 0)

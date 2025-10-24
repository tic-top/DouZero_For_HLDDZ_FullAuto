import GameHelper as gh
from GameHelper import GameHelper
import cv2
import numpy as np

GameHelper = GameHelper()

# img = cv2.imread("3.png")
# img = cv2.cvtColor(np.asarray(img), cv2.COLOR_BGR2RGB)
img, _ = GameHelper.Screenshot()
# 打印出大小
print(img.size)
# AttributeError: 'Image' object has no attribute 'shape'
img = gh.DrawRectWithText(img, (180, 560, 1050, 90), "test")
gh.ShowImg(img)

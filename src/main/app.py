# -*- coding: utf-8 -*-
"""Điểm vào ứng dụng: chuỗi màn hình hiệu ứng → cửa sổ chính."""
import tkinter as tk

from src.features.csv_to_vcf.ui import ContactsApp
from src.features.splash.matrix import MatrixWindow
from src.features.splash.system_check import SystemCheckWindow
from src.utils.dpi import enableHiDpiAwareness
from src.utils.resource_path import resourcePath

ICON_FILE = 'assets/icons/app-256.png'
APP_WIDTH, APP_HEIGHT = 750, 700
SLIDE_STEP_PX = 25
FADE_STEP = 0.06
SLIDE_DELAY_MS = 10


class AppLauncher:
    """Giữ trạng thái khởi chạy để các callback hiệu ứng dừng đúng lúc thoát."""

    def __init__(self, root, iconPhoto):
        self.root = root
        self.iconPhoto = iconPhoto
        self.isRunning = True

    def start(self):
        SystemCheckWindow(self.root, onComplete=self._startMatrix)

    def _startMatrix(self):
        if self.isRunning:
            MatrixWindow(self.root, onComplete=self._showMainApp)

    def _showMainApp(self):
        if not self.isRunning:
            return
        self.root.deiconify()
        screenWidth, screenHeight = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x = (screenWidth - APP_WIDTH) // 2
        startY, endY = -APP_HEIGHT, (screenHeight - APP_HEIGHT) // 2
        self.root.geometry(f'{APP_WIDTH}x{APP_HEIGHT}+{x}+{startY}')
        self.root.attributes('-alpha', 0.0)

        ContactsApp(self.root, iconPhoto=self.iconPhoto)
        self._animateScroll(x, endY, startY, 0.0)

    def _animateScroll(self, x, endY, currentY, currentAlpha):
        """Cửa sổ chính trượt từ trên xuống kèm hiệu ứng mờ dần."""
        if not self.isRunning:
            return
        if currentY >= endY:
            self.root.attributes('-alpha', 1.0)
            return
        newY = min(currentY + SLIDE_STEP_PX, endY)
        newAlpha = min(currentAlpha + FADE_STEP, 1.0)
        self.root.geometry(f'{APP_WIDTH}x{APP_HEIGHT}+{x}+{newY}')
        self.root.attributes('-alpha', newAlpha)
        self.root.after(SLIDE_DELAY_MS, lambda: self._animateScroll(x, endY, newY, newAlpha))


def _loadIcon():
    try:
        from PIL import Image, ImageTk
        return ImageTk.PhotoImage(Image.open(resourcePath(ICON_FILE)))
    except Exception as e:
        print(f"Lỗi tải hình ảnh: {e}")
        return None


def main():
    enableHiDpiAwareness()
    root = tk.Tk()
    root.withdraw()

    launcher = AppLauncher(root, _loadIcon())
    launcher.start()
    root.mainloop()

    launcher.isRunning = False
    try:
        if root.winfo_exists():
            root.destroy()
    except tk.TclError:
        pass  # cửa sổ đã bị hủy trước đó

import sys, os, dxcam, ctypes, win32gui, win32con
import numpy as n, cupy as c
from PyQt6.QtWidgets import QApplication as A, QMainWindow as M, QLabel as L
from PyQt6.QtCore import Qt as T, QThread as Q, pyqtSignal as S, QCoreApplication as C
from PyQt6.QtGui import QImage as I, QPixmap as P
from pynput import mouse, keyboard

# DLL Bootstrap for Nuitka
if getattr(sys, 'frozen', False):
    b = os.path.dirname(sys.executable)
    d = os.path.join(b, "CUDA_Bin")
    if os.path.exists(d): os.add_dll_directory(d)

X = 0x00000011

class CT(Q):
    f = S(n.ndarray)
    def __init__(self, p=None):
        super().__init__(p)
        self.cam = dxcam.create(output_color="RGB", max_buffer_len=1)
        self.r, self.a, self.g = True, True, 0.35
        self.lut = c.array([((i/255.0)**self.g)*255 for i in n.arange(0,256)]).astype("uint8")
    def run(self):
        self.cam.start(target_fps=0, video_mode=True)
        while self.r:
            if not self.a: self.msleep(50); continue
            fr = self.cam.get_latest_frame()
            if fr is not None:
                g = c.asarray(fr)
                p = c.take(self.lut, g)
                self.f.emit(p.get())
        self.cam.stop()

class NV(M):
    t = S(bool)
    e = S()
    def __init__(self):
        super().__init__()
        self.v = True
        self.setWindowFlags(T.WindowType.WindowStaysOnTopHint | T.WindowType.FramelessWindowHint | T.WindowType.Tool)
        self.setAttribute(T.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()
        self.l = L(self)
        self.l.setScaledContents(True)
        self.setCentralWidget(self.l)
        self.s()
        self.t.connect(self.x)
        self.e.connect(self.q)
        self.th = CT()
        self.th.f.connect(self.u)
        self.th.start()
        self.m = mouse.Listener(on_click=self.oc, daemon=True)
        self.m.start()
        self.k = keyboard.Listener(on_press=self.kp, daemon=True)
        self.k.start()
    def s(self):
        h = self.winId().__int__()
        ctypes.windll.user32.SetWindowDisplayAffinity(h, X)
        s = win32gui.GetWindowLong(h, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(h, win32con.GWL_EXSTYLE, s | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)
    def oc(self, x, y, b, p):
        if p and b == mouse.Button.x2:
            self.v = not self.v
            self.t.emit(self.v)
    def x(self, s):
        if s: self.th.a = True; self.showFullScreen()
        else: self.th.a = False; self.hide(); self.l.clear()
    def u(self, f):
        if not self.v: return
        h, w, ch = f.shape
        i = I(f.data, w, h, w * ch, I.Format.Format_RGB888)
        self.l.setPixmap(P.fromImage(i))
    def kp(self, k):
        if k == keyboard.Key.pause: self.e.emit()
    def q(self):
        self.th.r = False
        self.th.wait()
        self.m.stop()
        self.k.stop()
        C.quit()

if __name__ == "__main__":
    A.setHighDpiScaleFactorRoundingPolicy(T.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = A(sys.argv)
    w = NV()
    sys.exit(app.exec())
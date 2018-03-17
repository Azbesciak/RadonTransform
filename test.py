import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
from threading import Thread, Timer

x = np.linspace(0, 2 * np.pi, 300)
y = np.linspace(0, 2 * np.pi, 300).reshape(-1, 1)


class Test:
    def __init__(self) -> None:
        global x,y
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(8, 8))
        self.im1 = self.ax1.imshow(self.f(x, y), animated=True)
        self.im2 = None
        self.ani = self.ani2 = None

    def f(self, x, y):
        return np.sin(x) + np.cos(y)

    def updatefig1(self, *args):
        global x, y
        self.im1.set_array(self.f(x, y))
        return self.im1,

    def updatefig2(self, *args):
        global x,y
        self.im2.set_array(self.f(x, y))
        return self.im2,

    def run_ani(self):
        global x, y
        print("fired")
        self.im2 = self.ax2.imshow(self.f(x, y), animated=True)
        self.ani2 = animation.FuncAnimation(self.fig, self.updatefig2, interval=50, blit=True)


def update_x_y():
    global x, y
    while True:
        x += np.pi / 15.
        y += np.pi / 20.
        time.sleep(0.01)


def run_chart():
    t = Test()
    t.ani = animation.FuncAnimation(t.fig, t.updatefig1, interval=50, blit=True)
    t.run_ani()
    plt.show()


t1 = Thread(target=update_x_y)
t1.start()

run_chart()
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from threading import Timer

ani2 = None


class Test:

    def __init__(self) -> None:
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(8, 8))
        self.x = np.linspace(0, 2 * np.pi, 300)
        self.y = np.linspace(0, 2 * np.pi, 300).reshape(-1, 1)
        self.im1 = self.ax1.imshow(self.f(self.x, self.y), animated=True)
        self.im2 = None

    def f(self, x, y):
        return np.sin(x) + np.cos(y)

    def updatefig1(self, *args):
        self.x += np.pi / 15.
        self.y += np.pi / 20.
        self.im1.set_array(self.f(self.x, self.y))
        return self.im1,

    def updatefig2(self, *args):
        self.x += np.pi / 15.
        self.y += np.pi / 20.
        self.im2.set_array(self.f(self.x, self.y))
        return self.im2,

    def run_ani(self):
        global ani2
        print("fired")
        self.im2 = self.ax2.imshow(self.f(self.x, self.y), animated=True)
        ani2 = animation.FuncAnimation(self.fig, self.updatefig2, interval=50, blit=True)


def fire(t):
    plt.show()
    tim = Timer(5.0, t.run_ani)
    tim.start()
    ani = animation.FuncAnimation(t.fig, t.updatefig1, interval=50, blit=True)


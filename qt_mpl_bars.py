import sys
import traceback

from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, \
    QPushButton, QLineEdit, QLabel, QCheckBox, QDoubleSpinBox, QSpinBox
from PyQt5.QtGui import QIcon, QIntValidator, QDoubleValidator
from file_select import SelectFileButton

import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import time
from threading import Thread
import transformer as tr

label_margin = 10
input_margin = 40


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.left = 40
        self.top = 40
        self.title = 'Radon Transformation'
        self.width = 700
        self.height = 400
        self.file_select = self.run_btn = self.emitters_inp = self.alpha_inp = self.use_filter_cbx = None
        self.plot = None
        self.scanner = None
        self.is_im_ready = self.is_sin_ready = self.is_isin_ready = False
        self.is_im_working = self.is_sin_working = self.is_isin_working = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.init_plot()
        self.init_buttons()
        self.show()

    def init_plot(self):
        self.plot = PlotCanvas(self, width=5, height=4, dpi=170)
        self.plot.move(-80, -100)

    def init_buttons(self):
        self.add_file_select()
        self.add_run_button()
        self.add_emitters_input()
        self.add_alpha_input()
        self.add_use_filter_input()
        self.run_btn.clicked.connect(self.run_task)

    def run_task(self, e):
        try:
            self.run_btn.disabled = True
            if self.scanner:
                self.scanner.join()
            tr.params.set_values(self.alpha_inp.value(), self.emitters_inp.value(),
                                 self.use_filter_cbx.isChecked(), self.file_select.file_name)
            self.scanner = tr.Scanner(tr.params, self.plot, self.on_finish)
            self.plot.set_scanner(self.scanner)
            self.scanner.start()
        except Exception as e:
            traceback.print_exc()
            self.run_btn.disabled = False

    def on_finish(self):
        self.run_btn.disabled = False
        # self.plot.clean()

    def add_run_button(self):
        x = App.get_x_position(4)
        self.run_btn = QPushButton("Run", self)
        self.run_btn.clicked.connect(self.run_task)
        self.run_btn.move(x, input_margin)

    def add_file_select(self):
        x = App.get_x_position(3)
        self.file_select = SelectFileButton('Select file', self)
        self.file_select.move(x, input_margin)

    def add_emitters_input(self):
        x = App.get_x_position(1)
        emitters_lab = QLabel("Emitters number", self)
        emitters_lab.move(x, label_margin)
        self.emitters_inp = QSpinBox(self)
        self.emitters_inp.setMaximum(4000)
        self.emitters_inp.setValue(tr.params.emitters_num)
        self.emitters_inp.move(x, input_margin)

    def add_use_filter_input(self):
        x = App.get_x_position(2)
        self.use_filter_cbx = QCheckBox('Use sinogram filter', self)
        self.use_filter_cbx.setChecked(tr.params.use_filter)
        self.use_filter_cbx.move(x, input_margin)

    def add_alpha_input(self):
        x = App.get_x_position(0)
        alpha_lab = QLabel('Alpha value', self)
        alpha_lab.move(x, label_margin)
        self.alpha_inp = QDoubleSpinBox(self)
        self.alpha_inp.setValue(tr.params.alpha)
        self.alpha_inp.move(x, input_margin)

    @staticmethod
    def get_x_position(index):
        return index * 120 + 50


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=8, dpi=100):
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(1, 3, figsize=(width, height), dpi=dpi)
        self.ax1.set_axis_off()
        self.ax2.set_axis_off()
        self.ax3.set_axis_off()
        self.im1 = self.im2 = self.im3 = None
        self.ani2 = self.ani3 = None
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.scanner = None
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        zeros = np.zeros((400, 400))
        self.ax1.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.ax2.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.ax3.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.draw()

    def set_scanner(self, scanner):
        self.scanner = scanner
        if self.ani2:
            self.ani2.event_source.stop()
        if self.ani3:
            self.ani3.event_source.stop()
        self.ani2 = animation.FuncAnimation(self.fig, self.update_sin, interval=50, blit=True)
        self.ani3 = animation.FuncAnimation(self.fig, self.update_isin, interval=50, blit=True)

    def on_new_scan(self, image):
        self.ax1.imshow(image, cmap=plt.cm.Greys_r)

    def on_sinogram(self, sinogram):
        self.im2 = self.ax2.imshow(sinogram, cmap=plt.cm.Greys_r, animated=True)

    def on_isinogram(self, i_sin):
        self.im3 = self.ax3.imshow(i_sin, cmap=plt.cm.Greys_r, animated=True)

    def update_sin(self, *f):
        if self.im2 is not None and self.scanner.im2c:
            self.scanner.im2c = False
            self.im2.set_data(self.scanner.sinogram)
            self.im3.norm.autoscale(self.scanner.sinogram)
        return self.im2,

    def update_isin(self, *f):
        if self.im3 is not None and self.scanner.im3c:
            self.scanner.im3c = False
            self.im3.set_data(self.scanner.i_sin)
            self.im3.norm.autoscale(self.scanner.i_sin)
        return self.im3,

    def clean(self):
        self.ani3 = self.ani2 = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
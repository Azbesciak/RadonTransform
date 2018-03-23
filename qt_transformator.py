import sys
import time
import traceback
from threading import Thread

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pydicom
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import transformer as tr
from DicomModal import DicomDialog
from file_select import SelectFileButton

label_margin = 10
input_margin = 40


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.left = 40
        self.top = 40
        self.title = 'Radon Transformation'
        self.width = 1000
        self.height = 800
        self.file_select = self.run_btn = self.emitters_inp = self.alpha_inp = \
            self.use_filter_cbx = self.use_gauss = self.dicom_btn = None
        self.plot = None
        self.scanner = None
        self.is_working = False
        self.image = None
        self.ds = None
        self.dicom_modal = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.init_plot()
        self.init_buttons()
        self.show()

    def init_plot(self):
        self.plot = PlotCanvas(self, width=5, height=4, dpi=230)
        self.plot.move(-100, -50)

    def init_buttons(self):
        self.add_file_select()
        self.add_run_button()
        self.add_emitters_input()
        self.add_alpha_input()
        self.add_use_filter_input()
        self.add_use_gauss_ckbx()
        self.add_edit_dicom_button()
        self.run_btn.clicked.connect(self.run_task)

    def run_task(self, e):
        try:
            if self.is_working:
                return
            self.is_working = True
            print("New task started.")

            self.run_btn.setDisabled(True)
            self.file_select.setDisabled(True)
            self.plot.update_medium_error_value()
            tr.params.set_values(self.alpha_inp.value(), self.emitters_inp.value(),
                                 self.use_filter_cbx.isChecked(), self.file_select.file_name,
                                 self.use_gauss.isChecked())
            self.scanner = tr.Scanner(tr.params, self.plot, on_finish=self.on_finish, image=self.image)
            self.plot.init_new_scan(self.scanner)
            Thread(target=lambda: self.scanner.watch_changes()).start()
        except Exception as e:
            traceback.print_exc()
            self.on_finish(0)

    def on_finish(self, sleep=0.05):
        print("finished work!")
        self.is_working = False
        self.run_btn.setDisabled(False)
        self.file_select.setDisabled(False)
        time.sleep(sleep)
        self.plot.clean()

    def add_edit_dicom_button(self):
        x = App.get_x_position(6)
        self.dicom_btn = QPushButton("Edit DICOM", self)
        self.dicom_btn.clicked.connect(self.show_dicom_edit_modal)
        self.dicom_btn.setDisabled(True)
        self.dicom_btn.move(x, input_margin)

    def add_run_button(self):
        x = App.get_x_position(5)
        self.run_btn = QPushButton("Run", self)
        self.run_btn.clicked.connect(self.run_task)
        self.run_btn.move(x, input_margin)

    def add_file_select(self):
        x = App.get_x_position(4)
        self.file_select = SelectFileButton('Select file', self, listener=self.on_file_select)
        self.file_select.move(x, input_margin)

    def add_use_gauss_ckbx(self):
        x = App.get_x_position(3)
        self.use_gauss = QCheckBox('Use Gauss\nfor tomograph', self)
        self.use_gauss.setChecked(tr.params.use_filter)
        self.use_gauss.move(x, input_margin)

    def add_use_filter_input(self):
        x = App.get_x_position(2)
        self.use_filter_cbx = QCheckBox('Use sinogram\nfilter', self)
        self.use_filter_cbx.setChecked(tr.params.use_filter)
        self.use_filter_cbx.move(x, input_margin)

    def add_emitters_input(self):
        x = App.get_x_position(1)
        emitters_lab = QLabel("Emitters number", self)
        emitters_lab.move(x, label_margin)
        self.emitters_inp = QSpinBox(self)
        self.emitters_inp.setMaximum(4000)
        self.emitters_inp.setValue(tr.params.emitters_num)
        self.emitters_inp.move(x, input_margin)

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

    def on_file_select(self, file_name):
        if file_name.lower().endswith((".dc3", ".dcm", ".dic")):
            self.ds = pydicom.dcmread(file_name)
            self.image = self.ds.pixel_array
            self.dicom_btn.setDisabled(False)
        else:
            self.image = tr.read_image(file_name)
            self.ds = None
            self.dicom_btn.setDisabled(True)
        self.plot.set_image(self.image)

    def show_dicom_edit_modal(self):
        if self.dicom_modal is None and self.ds is not None:
            self.dicom_modal = DicomDialog(self, self.clear_dicom_modal, self.file_select.file_name, self.ds)
            self.dicom_modal.setModal(False)
            self.dicom_modal.exec_()

    def clear_dicom_modal(self):
        self.dicom_modal = None


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=8, dpi=100):
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(1, 3, figsize=(width, height), dpi=dpi)
        self.ax1.set_axis_off()
        self.ax2.set_axis_off()
        self.ax3.set_axis_off()
        self.image = None
        self.medium_error = 0
        self.medium_error_label = None
        self.im1 = self.im2 = self.im3 = None
        self.ani2 = self.ani3 = None
        self.ta2 = self.ta3 = None
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.create_error_label(parent)
        self.scanner = None
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        zeros = np.zeros((400, 400))
        self.im1 = self.ax1.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.im2 = self.ax2.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.im3 = self.ax3.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.draw()

    def init_new_scan(self, scanner):
        self.plot()
        self.scanner = scanner
        self.clean()
        self.ani2 = animation.FuncAnimation(self.fig, self.update_sin, interval=50, blit=True)
        self.ani3 = animation.FuncAnimation(self.fig, self.update_isin, interval=50, blit=True)

    def set_image(self, image):
        self.image = image
        self.im1 = self.ax1.imshow(image, cmap=plt.cm.Greys_r, animated=True)
        self.draw()

    def on_new_scan(self, image):
        self.image = image
        print("new scan!")
        self.update_chart(self.im1, image)

    def on_sinogram(self, sinogram):
        print("new sinogram came")
        self.im2 = self.ax2.imshow(sinogram, cmap=plt.cm.Greys_r, animated=True)

    def on_isinogram(self, i_sin):
        print("reverse transformation started")
        self.im3 = self.ax3.imshow(i_sin, cmap=plt.cm.Greys_r, animated=True)

    def update_sin(self, _):
        if self.scanner.im2c:
            self.scanner.im2c = False
            self.update_chart(self.im2, self.scanner.sinogram)
        return self.im2,

    def update_isin(self, _):
        if self.scanner.im3c:
            self.scanner.im3c = False
            self.update_chart(self.im3, self.scanner.i_sin)
            self.count_medium_error()
        return self.im3,

    def count_medium_error(self):
        self.medium_error = self.get_medium_squared_error(self.image, self.scanner.i_sin)
        self.update_medium_error_value(self.medium_error)

    @staticmethod
    def update_chart(im, data):
        im.set_data(data)
        im.norm.autoscale(data)

    def create_error_label(self, parent):
        self.medium_error_label = QLabel(parent)
        self.medium_error_label.move(700, 60)
        self.medium_error_label.setFixedWidth(200)

    def update_medium_error_value(self, value=0):
        self.medium_error_label.setText("medium square error: %6.4f" % value)

    def clean(self):
        if self.scanner is not None:
            self.count_medium_error()
        if self.ani2 is not None:
            self.ani2.event_source.stop()
        if self.ani3 is not None:
            self.ani3.event_source.stop()
        self.ani3 = self.ani2 = None

    @staticmethod
    def get_medium_squared_error(original, reconstructed):
        if original is not None and reconstructed is not None:
            original_copy = original - original.min()
            reconstructed_copy = reconstructed - reconstructed.min()
            org_copy_max = original_copy.max()
            rec_copy_max = reconstructed_copy.max()
            if rec_copy_max > 0 and org_copy_max > 0 and rec_copy_max is not org_copy_max:
                reconstructed_copy /= (rec_copy_max / org_copy_max)
            dif = original_copy - reconstructed_copy
            dif **= 2
            return dif.sum() / dif.size
        else:
            return 0


if __name__ == '__main__':
    app = QApplication(sys.argv)
    res = 0
    try:
        ex = App()
        res = app.exec_()
    except Exception:
        print("exiting")
    sys.exit(res)

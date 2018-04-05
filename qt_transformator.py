import sys
import time
import traceback
from PyQt5.QtCore import Qt
from threading import Thread

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pydicom
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from qtpy import QtWidgets

import transformer as tr
from DicomModal import DicomDialog
from dicom_creator import create_dcm_file
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
            self.use_filter_cbx = self.interactive_mode = self.dicom_btn = self.slider = None
        self.is_interactive = True
        self.plot = None
        self.scanner = None
        self.is_working = False
        self.image = None
        self.ds = None
        self.dicom_modal = None
        self.result_table = None
        self.current_row = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.init_plot()
        self.init_buttons()
        self.init_table()
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
        self.add_interactive_mode_ckbx()
        self.add_edit_dicom_button()
        self.run_btn.clicked.connect(self.run_task)
        self.add_slider()

    def add_slider(self):
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.move(340, 700)
        self.slider.setTickInterval(180)
        self.slider.setSingleStep(1)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setFixedWidth(300)
        self.slider.setDisabled(True)
        self.slider.valueChanged.connect(self.on_slider_value_change)

    def run_task(self, e):
        try:
            if self.is_working:
                return
            self.is_working = True
            print("New task started.")
            self.slider.setDisabled(True)
            self.run_btn.setDisabled(True)
            self.file_select.setDisabled(True)
            self.plot.update_medium_error_value()
            self.is_interactive = self.interactive_mode.isChecked()
            tr.params.set_values(self.alpha_inp.value(), self.emitters_inp.value(),
                                 self.use_filter_cbx.isChecked(), self.file_select.file_name)
            self.scanner = tr.Scanner(tr.params, self.plot, on_finish=self.on_finish, image=self.image)
            self.plot.init_new_scan(self.scanner)
            Thread(target=lambda: self.scanner.watch_changes()).start()
        except Exception:
            traceback.print_exc()
            self.on_finish(True)

    def on_finish(self, wasException=False):
        print("finished work!")
        self.is_working = False
        self.run_btn.setDisabled(False)
        self.file_select.setDisabled(False)
        if not self.is_interactive or wasException:
            time.sleep(0.05)
            self.plot.clean()
        elif self.is_interactive:
            self.slider.setDisabled(False)
        if not wasException:
            self.add_row_to_table(file=tr.params.image_name.split("/")[-1], alpha=tr.params.alpha,
                                  emitters=tr.params.emitters_num, error=self.scanner.square_error)

    def on_slider_value_change(self):
        value = self.slider.value()
        if self.scanner is not None:
            self.scanner.get_snapshot(value)

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

    def add_interactive_mode_ckbx(self):
        x = App.get_x_position(3)
        self.interactive_mode = QCheckBox('Interactive\nmode', self)
        self.interactive_mode.setChecked(self.is_interactive)
        self.interactive_mode.move(x, input_margin)

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

    def init_table(self):
        self.result_table = QTableWidget(self)
        self.result_table.setRowCount(1)
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["File", "Alpha", "Emitters", "MS Error"])
        self.result_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        [self.result_table.setColumnWidth(i, 100) for i in [0,3]]
        [self.result_table.setColumnWidth(i, 70) for i in [1,2]]
        self.result_table.setFixedWidth(361)
        self.result_table.setFixedHeight(200)
        self.result_table.move(50, 100)

    def add_row_to_table(self, file, alpha, emitters, error):
        for (i, t) in enumerate([file, alpha, emitters, error]):
            self.result_table.setItem(self.current_row, i, QTableWidgetItem(str(t)))
        self.current_row += 1
        self.result_table.setRowCount(self.current_row+1)

    @staticmethod
    def get_x_position(index):
        return index * 120 + 50

    def on_file_select(self, file_name):
        try:
            if file_name.lower().endswith((".dc3", ".dcm", ".dic")):
                self.ds = pydicom.dcmread(file_name, force=True)
                self.ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                self.image = tr.normalize_img(self.ds.pixel_array)
                self.dicom_btn.setDisabled(False)
            else:
                self.image = tr.read_image(file_name)
                self.ds = create_dcm_file(np.array(self.image))
                self.dicom_btn.setDisabled(False)
                # self.dicom_btn.setDisabled(True)
            self.plot.set_image(self.image)
        except Exception:
            traceback.print_exc()

    def show_dicom_edit_modal(self):
        if self.dicom_modal is None and self.ds is not None:
            self.dicom_modal = DicomDialog(self, self.clear_dicom_modal, self.file_select.file_name, self.ds)
            self.dicom_modal.setModal(False)
            self.dicom_modal.exec_()

    def clear_dicom_modal(self):
        self.dicom_modal = None


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=8, dpi=100):
        self.fig, _ = plt.subplots(12, 9, figsize=(width, height), dpi=dpi)
        self.ax1 = plt.subplot2grid((12, 9), (3, 0), rowspan=9, colspan=3)
        self.ax2 = plt.subplot2grid((12, 9), (3, 3), rowspan=9, colspan=3)
        self.ax3 = plt.subplot2grid((12, 9), (3, 6), rowspan=9, colspan=3)
        self.ax_err = None
        self.prepare_error_chart()
        self.ax1.set_axis_off()
        self.ax2.set_axis_off()
        self.ax3.set_axis_off()
        self.image = None
        self.medium_error_label = None
        self.im1 = self.im2 = self.im3 = self.im_err = None
        self.ani2 = self.ani3 = self.ani_err = None
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

    def prepare_error_chart(self):
        plt.subplot2grid((12, 9), (0, 0), colspan=9, rowspan=3).set_axis_off()
        self.ax_err = plt.subplot2grid((12, 9), (1, 6), colspan=3, rowspan=2)
        for label in (self.ax_err.get_xticklabels() + self.ax_err.get_yticklabels()):
            label.set_fontname('Arial')
            label.set_fontsize(5)
        self.ax_err.set_ylim([0,1])
        self.ax_err.set_yticks(np.arange(0, 1.1, 0.2))
        # self.ax_err.setti

    def set_iterations(self, iterations):
        self.ax_err.set_xlim([0, iterations])
        self.ax_err.set_xticks(np.arange(0, iterations+1, iterations//5))

    def plot(self):
        zeros = np.zeros((400, 400))
        self.im1 = self.ax1.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.im2 = self.ax2.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.im3 = self.ax3.imshow(zeros, cmap=plt.cm.Greys_r, animated=True)
        self.im_err = self.ax_err.plot([])[0]
        self.draw()

    def init_new_scan(self, scanner):
        self.plot()
        self.scanner = scanner
        self.clean()
        self.ani2 = animation.FuncAnimation(self.fig, self.update_sin, interval=50, blit=True)
        self.ani3 = animation.FuncAnimation(self.fig, self.update_isin, interval=50, blit=True)
        self.ani_err = animation.FuncAnimation(self.fig, self.update_error, interval=50, blit=True, repeat=False)

    def set_image(self, image):
        self.image = image
        self.im1 = self.ax1.imshow(image, cmap=plt.cm.Greys_r, animated=True)
        self.draw()

    def on_new_scan(self, image, iterations):
        self.image = image
        print("new scan!")
        self.update_chart(self.im1, image)
        self.set_iterations(iterations)

    def on_sinogram(self, sinogram):
        print("new sinogram came")
        self.im2 = self.ax2.imshow(sinogram, cmap=plt.cm.Greys_r, animated=True)

    def on_isinogram(self, i_sin):
        print("reverse transformation started")
        self.im3 = self.ax3.imshow(i_sin, cmap=plt.cm.Greys_r, animated=True)

    def update_sin(self, _):
        if self.scanner.refresh_sinogram:
            self.scanner.refresh_sinogram = False
            self.update_chart(self.im2, self.scanner.sinogram)
        return self.im2,

    def update_isin(self, _):
        if self.scanner.refresh_isin:
            self.scanner.refresh_isin = False
            self.update_chart(self.im3, self.scanner.i_sin)
            self.count_medium_error(self.scanner.square_error)
        return self.im3,

    def update_error(self, _):
        [self.im_err] = self.ax_err.plot(self.scanner.errors_history)
        return self.im_err,

    def count_medium_error(self, value=0):
        self.update_medium_error_value(value)

    @staticmethod
    def update_chart(im, data):
        im.set_data(data)
        im.norm.autoscale(data)

    def create_error_label(self, parent):
        self.medium_error_label = QLabel(parent)
        self.medium_error_label.move(700, 80)
        self.medium_error_label.setFixedWidth(200)
        self.update_medium_error_value()

    def update_medium_error_value(self, value=0):
        self.medium_error_label.setText("Medium square error: %6.4f" % value)

    def clean(self):
        if self.scanner is not None:
            self.count_medium_error()
        if self.ani2 is not None:
            self.ani2.event_source.stop()
        if self.ani3 is not None:
            self.ani3.event_source.stop()
        self.ani3 = self.ani2 = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    res = 0
    try:
        ex = App()
        res = app.exec_()
    except Exception:
        traceback.print_exc()
        print("exiting")
    sys.exit(res)

import traceback

import moment
import pydicom
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import *


# (0008, 0020) Study Date                          DA: '20040119'
# (0008, 0012) Instance Creation Date              DA: '20040119'
# (0008, 0013) Instance Creation Time              TM: '072731'
# (0008, 0014) Instance Creator UID                UI: 1.3.6.1.4.1.5962.3
# (0010, 0010) Patient's Name                      PN: 'CompressedSamples^CT1'
# (0010, 0020) Patient ID                          LO: 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
# (0010, 0030) Patient's Birth Date                DA: ''
# (0010, 0040) Patient's Sex                       CS: 'O'
# (0010, 1010) Patient's Age                       AS: '000Y'
# (0010, 1030) Patient's Weight                    DS: "0.000000"
# (0020, 4000) Image Comments                      LT: 'Uncompressed'

def get_x(i):
    return 35 + i * 140


def get_y(i):
    return 30 + i * 50


def get_margin_y(i):
    return get_y(i) - 15


def get_date(date):
    if date and len(date) > 0:
        date = moment.date(date, "%Y%m%d")
        return QDate(date.year, date.month, date.day)
    return None


class DicomDialog(QDialog):

    def __init__(self, parent, on_close, file_name, ds):
        super().__init__(parent)
        self.on_close = on_close
        self.study_date = self.patient_name = self.patient_id = self.patient_birth_date = \
            self.patient_sex = self.patient_age = self.patient_weight = self.comment = self.save_btn = None
        self.title = 'Dicom edit - %s' % file_name
        self.ds = ds
        self.setFixedWidth(340)
        self.setFixedHeight(430)
        self.initUi()

    def add_at(self, input, x, y, label):
        input.move(get_x(x), get_y(y))
        QLabel(label, self).move(get_x(x), get_margin_y(y))

    def initUi(self):
        self.add_study_date()
        self.add_patient_name()
        self.add_patient_id()
        self.add_birth_of_date()
        self.add_patient_sex()
        self.add_patient_age()
        self.add_patient_weight()
        self.add_image_comment()
        self.add_save_btn()
        self.show()

    def add_save_btn(self):
        self.save_btn = QPushButton("Save file", self)
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.move(220, 385)

    def add_image_comment(self):
        self.comment = QTextEdit(self)
        self.comment.setFixedWidth(270)
        if "ImageComments" in self.ds:
            self.comment.setText(str(self.ds.ImageComments))
        self.add_at(self.comment, 0, 3, "Image comment")

    def add_patient_weight(self):
        self.patient_weight = QDoubleSpinBox(self)
        self.patient_weight.setMaximum(200)
        if "PatientWeight" in self.ds:
            self.patient_weight.setValue(float(self.ds.PatientWeight))
        self.add_at(self.patient_weight, 1.5, 1, "Patient weight")

    def add_patient_age(self):
        self.patient_age = QSpinBox(self)
        if "PatientAge" in self.ds:
            self.patient_age.setValue(int(self.ds.PatientAge))
        self.add_at(self.patient_age, 1, 1, "Patient age")
        self.patient_age.setMaximum(150)

    def add_patient_sex(self):
        self.patient_sex = QLineEdit(self)
        if "PatientSex" in self.ds:
            self.patient_sex.setText(str(self.ds.PatientSex))
        self.add_at(self.patient_sex, 0, 1, "Patient sex")

    def add_birth_of_date(self):
        self.patient_birth_date = QDateTimeEdit(self)
        if "PatientBirthDate" in self.ds:
            date = get_date(self.ds.PatientBirthDate)
            if date is not None:
                self.patient_birth_date.setDate(date)
        self.add_at(self.patient_birth_date, 1, 2, "Date of birth")

    def add_patient_id(self):
        self.patient_id = QLineEdit(self)
        if "PatientID" in self.ds:
            self.patient_id.setText(str(self.ds.PatientID))
        self.add_at(self.patient_id, 0, 0, "Patient Id")

    def add_patient_name(self):
        self.patient_name = QLineEdit(self)
        if "PatientName" in self.ds:
            self.patient_name.setText(str(self.ds.PatientName))
        self.add_at(self.patient_name, 1, 0, "Patient name")

    def add_study_date(self):
        self.study_date = QDateTimeEdit(self)
        if "StudyDate" in self.ds:
            date = get_date(self.ds.StudyDate)
            if date is not None:
                self.study_date.setDate(date)
        self.add_at(self.study_date, 0, 2, "Study date")

    def closeEvent(self, event):
        self.on_close()

    def set_new_data(self):
        with self.ds as x:
            x.PatientName = self.patient_name.text()
            x.PatientID = self.patient_id.text()
            x.PatientSex = self.patient_sex.text()
            x.PatientAge = str(self.patient_age.value())
            x.PatientWeight = str(self.patient_weight.value())
            x.ImageComments = self.comment.toPlainText()
            x.StudyDate = self.study_date.date().toString("yyyyMMdd")
            x.PatientBirthDate = self.patient_birth_date.date().toString("yyyyMMdd")

    def save_file(self):
        file_name = QFileDialog.getSaveFileName(self, 'Save file as...', filter="DICOM (*.dc3 *.dcm *.dic)")
        try:
            self.set_new_data()
            if len(file_name[0]) > 0:
                pydicom.filewriter.write_file(file_name[0], self.ds)
        except Exception as e:
            traceback.print_exc()
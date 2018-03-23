from PyQt5.QtWidgets import QPushButton, QFileDialog


class SelectFileButton(QPushButton):

    def __init__(self, name, parent, listener=None):
        super().__init__(name, parent)
        self.file_name = None
        self.clicked.connect(self.openFileNameDialog)
        self.listener = listener
        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.file_name, _ = QFileDialog.getOpenFileName(self, "Select file", "",
                                                        "All Files (*);;"
                                                        "Images (*.jpeg *.jpg *.bmp *.png);;"
                                                        "DICOM (*.dc3 *.dcm *.dic)",
                                                        options=options)
        if self.file_name:
            print("selected %s" % self.file_name)
            if self.listener:
                self.listener(self.file_name)

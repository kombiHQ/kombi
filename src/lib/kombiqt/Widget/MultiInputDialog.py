from Qt import QtWidgets, QtCore

class MultiInputDialog(QtWidgets.QDialog):
    """
    Provides a generic input dialog with support for multiple inputs.

    Example:
    promptDialog = MultiInputDialog(
        {
            'key a': 'default value',
            'key b': '',
            'key c': True,
            'key d': ['a', 'b', 'c']
        },
        title='dialog title',
        helpText='help text'
    )

    # when Ok button is pressed
    if promptDialog.exec_():
        print(promptDialog.outputDict())
    """

    def __init__(self, inputDict, title="", helpText="", showCancelButton=True, minimumWidth=600, **kwargs):
        """
        Create an multi input dialog object.
        """
        super(MultiInputDialog, self).__init__(**kwargs)

        assert isinstance(inputDict, dict), 'Invalid input dict!'
        self.setWindowTitle(title)
        self.setMinimumWidth(minimumWidth)

        self.__inputs = {}
        formLayout = QtWidgets.QFormLayout()
        for key, value in inputDict.items():

            if isinstance(value, (list, tuple)):
                self.__inputs[key] = QtWidgets.QComboBox(self)
                for item in value:
                    self.__inputs[key].addItem(str(item), item)

            elif isinstance(value, bool):
                self.__inputs[key] = QtWidgets.QCheckBox('', self)
                if value:
                    self.__inputs[key].setCheckState(QtCore.Qt.Checked)

            elif isinstance(value, QtWidgets.QWidget):
                self.__inputs[key] = value

            else:
                self.__inputs[key] = QtWidgets.QLineEdit(str(value), self)

            formLayout.addRow(str(key), self.__inputs[key])

        self.__buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel if showCancelButton else QtWidgets.QDialogButtonBox.Ok)
        self.__buttonBox.accepted.connect(self.accept)
        self.__buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        if helpText:
            mainLayout.addWidget(QtWidgets.QLabel(helpText), 0)
            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.HLine)
            mainLayout.addWidget(frame, 0)

        mainLayout.addLayout(formLayout, 1)
        mainLayout.addWidget(self.__buttonBox)

        self.setLayout(mainLayout)

    def outputDict(self):
        """
        Return a dict with all values held by the inputs.
        """
        result = {}
        for key, widget in self.__inputs.items():
            if isinstance(widget, QtWidgets.QComboBox):
                result[key] = widget.currentData()
            elif isinstance(widget, QtWidgets.QTextEdit):
                result[key] = str(widget.toPlainText())
            elif isinstance(widget, QtWidgets.QCheckBox):
                result[key] = widget.isChecked()
            else:
                result[key] = str(widget.text())
        return result

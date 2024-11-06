from Qt import QtWidgets

class ComboBoxInputDialog(QtWidgets.QDialog):
    """
    Provides a generic combo box prompt dialog.

    Example:
    promptDialog = ComboBoxInputDialog(
        [
            'a',
            'b',
            'c',
        ],
        title='dialog title',
        helpText='help text'
    )

    # when Ok button is pressed
    if promptDialog.exec_():
        print(promptDialog.currentText())

    """
    def __init__(self, presets=[], title="", helpText="", editable=True, minimumWidth=600, **kwargs):
        """
        Create a combo box input dialog object.
        """
        super(ComboBoxInputDialog, self).__init__(**kwargs)

        assert isinstance(presets, (list, tuple)), 'Invalid input list!'
        self.setWindowTitle(title)
        self.setMinimumWidth(minimumWidth)

        self.__comboBox = QtWidgets.QComboBox()
        for preset in presets:
            self.__comboBox.addItem(str(preset))
        self.__comboBox.setEditable(editable)
        self.__comboBox.completer().setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

        self.__buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.__buttonBox.accepted.connect(self.accept)
        self.__buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        if helpText:
            mainLayout.addWidget(QtWidgets.QLabel(helpText), 0)

        mainLayout.addWidget(self.__comboBox)
        mainLayout.addWidget(self.__buttonBox)

        self.setLayout(mainLayout)

    def currentText(self):
        """
        Return the current text in the combo box.
        """
        return str(self.__comboBox.currentText())

import os
from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual
from .PresetsOptionVisual import _ComboBox
from ..Resource import Resource


class DirectoryPathOptionVisual(OptionVisual):
    """
    Implement the widget for a text option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create DirectoryPathOptionVisual object.
        """
        super().__init__(optionName, optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        presets = [
            str(self.optionValue())
        ]
        if 'presets' in self.uiHints():
            for preset in self.uiHints()['presets']:
                if preset in presets:
                    continue
                presets.append(preset)

        self.__editableWidget = _ComboBox(self) if len(presets) > 1 else QtWidgets.QLineEdit(str(self.optionValue()))
        self.__editableWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
        if len(presets) > 1:
            self.__editableWidget.addItems(presets)
            self.__editableWidget.setEditable(True)

        folderPicker = QtWidgets.QPushButton(self.uiHints().get('label', 'Select Directory'))
        folderPicker.setFocusPolicy(QtCore.Qt.NoFocus)
        folderPicker.clicked.connect(self.__onPickerSelectDir)
        folderPicker.setIcon(Resource.icon('icons/folder.png'))

        signal = self.__editableWidget.currentTextChanged if len(presets) > 1 else self.__editableWidget.textChanged
        signal.connect(self.__onValueChanged)
        mainLayout.addWidget(self.__editableWidget, 10)
        mainLayout.addWidget(folderPicker, 0)

    def __onValueChanged(self, *_):
        """
        Callback triggered when the text input is changed.
        """
        if isinstance(self.__editableWidget, QtWidgets.QLineEdit):
            self.valueChanged.emit(self.__editableWidget.text())
        else:
            self.valueChanged.emit(self.__editableWidget.currentText())

    def __onPickerSelectDir(self, *args, **kwargs):
        """
        Callback triggered when select directory button is pressed.
        """
        currentPath = self.__editableWidget.text() if isinstance(self.__editableWidget, QtWidgets.QLineEdit) else self.__editableWidget.currentText()
        initialPath = currentPath if os.path.exists(currentPath) else ""

        selectedFolder = QtWidgets.QFileDialog().getExistingDirectory(
            self,
            "Select Directory",
            initialPath,
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if not selectedFolder:
            return

        if isinstance(self.__editableWidget, QtWidgets.QLineEdit):
            self.__editableWidget.setText(selectedFolder)
        else:
            self.__editableWidget.setCurrentText(selectedFolder)


# registering option visual
OptionVisual.register('directoryPath', DirectoryPathOptionVisual)

# registering examples
OptionVisual.registerExample('directoryPath', 'default', '/file/path')
OptionVisual.registerExample('directoryPath', 'presets', '', {'presets': ['/filePathA', '/filePathB']})
OptionVisual.registerExample('directoryPath', 'buttonLabel', '', {'label': '...'})

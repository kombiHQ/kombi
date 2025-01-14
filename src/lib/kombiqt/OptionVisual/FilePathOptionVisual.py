import os
from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual
from .PresetsOptionVisual import _ComboBox
from ..Resource import Resource


class FilePathOptionVisual(OptionVisual):
    """
    Implement the widget for a text option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create FilePathOptionVisual object.
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

        filePicker = QtWidgets.QPushButton('Select File')
        filePicker.clicked.connect(self.__onPickerSelectFile)
        filePicker.setIcon(Resource.icon('icons/elements/base.png'))

        signal = self.__editableWidget.currentTextChanged if len(presets) > 1 else self.__editableWidget.textChanged
        signal.connect(self.__onValueChanged)
        mainLayout.addWidget(self.__editableWidget, 10)
        mainLayout.addWidget(filePicker, 0)

    def __onValueChanged(self, *_):
        """
        Callback triggered when the text input is changed.
        """
        if isinstance(self.__editableWidget, QtWidgets.QLineEdit):
            self.valueChanged.emit(self.__editableWidget.text())
        else:
            self.valueChanged.emit(self.__editableWidget.currentText())

    def __onPickerSelectFile(self, *args, **kwargs):
        """
        Callback triggered when select directory button is pressed.
        """
        currentPath = self.__editableWidget.text() if isinstance(self.__editableWidget, QtWidgets.QLineEdit) else self.__editableWidget.currentText()
        initialPath = currentPath if os.path.exists(currentPath) else ""

        extensions = self.uiHints().get('allowedExtensions', [])
        selectedFile = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.uiHints().get("title", "Select file"),
            initialPath,
            ';;'.join(map(lambda x: "{ext} (*.{ext})".format(ext=x), extensions))
        )

        if not selectedFile:
            return
        selectedFile = selectedFile[0]

        if isinstance(self.__editableWidget, QtWidgets.QLineEdit):
            self.__editableWidget.setText(selectedFile)
        else:
            self.__editableWidget.setCurrentText(selectedFile)


OptionVisual.register('filePath', FilePathOptionVisual)

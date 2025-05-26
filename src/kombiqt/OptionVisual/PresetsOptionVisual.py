from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual


class PresetsOptionVisual(OptionVisual):
    """
    Implement the widget for a presets visual.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create PresetsOptionVisual object.
        """
        super().__init__(optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        self.__mainWidget = _ComboBox(self)
        self.__mainWidget.setFocusPolicy(QtCore.Qt.ClickFocus)

        presets = [
            str(self.optionValue())
        ]

        # preset list
        for preset in self.uiHints().get('presets', []):
            if preset in presets:
                continue
            presets.append(preset)

        self.__mainWidget.addItems(presets)
        self.__mainWidget.currentTextChanged.connect(self.__onValueChanged)

        mainLayout.addWidget(self.__mainWidget)

        # editable presets
        if self.uiHints().get('editable'):
            self.__mainWidget.setEditable(True)
        # otherwise, making sure it does not expand to use the whole width
        else:
            self.__mainWidget.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
            mainLayout.addStretch()

        # read only
        self.__mainWidget.setEnabled(not self.uiHints().get('readOnly', False))

    def __onValueChanged(self):
        """
        Triggered when the combobox is changed.
        """
        value = self.__mainWidget.currentText()
        self.valueChanged.emit(value)


class _ComboBox(QtWidgets.QComboBox):
    """
    Internal combo box implementation necessary to disable the scrolling wheel.
    """

    def wheelEvent(self, event):
        """
        This is necessary to avoid the value being accidentally changed by scrolling the UI.
        """
        event.ignore()


# registering option visual
OptionVisual.register('presets', PresetsOptionVisual)

# registering examples
OptionVisual.registerExample('presets', 'default', '', {'visual': 'presets', 'presets': ['A', 'B', 'C']})
OptionVisual.registerExample('presets', 'editable', '', {'visual': 'presets', 'presets': ['A', 'B', 'C'], 'editable': True})
OptionVisual.registerExample('presets', 'readOnly', '', {'visual': 'presets', 'presets': ['A', 'B', 'C'], 'readOnly': True})

from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual


class PresetsOptionVisual(OptionVisual):
    """
    Implement the widget for a presets visual.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create PresetsOptionVisual object.
        """
        super().__init__(optionName, optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QVBoxLayout()
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

        # editable presets
        if self.uiHints().get('editable'):
            self.__mainWidget.setEditable(True)

        self.__mainWidget.addItems(presets)
        self.__mainWidget.currentTextChanged.connect(self.__onValueChanged)

        mainLayout.addWidget(self.__mainWidget)

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

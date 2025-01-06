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

        self.__mainWidget = QtWidgets.QComboBox(self)
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


OptionVisual.register('presets', PresetsOptionVisual)

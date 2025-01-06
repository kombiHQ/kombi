from Qt import QtWidgets
from .OptionVisual import OptionVisual


class BoolOptionVisual(OptionVisual):
    """
    Implement the widget for a boolean option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create BoolOptionVisual object.
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

        self.__mainWidget = QtWidgets.QCheckBox()
        self.__mainWidget.setChecked(self.optionValue())
        self.__mainWidget.stateChanged.connect(self.__onValueChanged)

        mainLayout.addWidget(self.__mainWidget)

    def __onValueChanged(self):
        """
        Triggered when the checkbox is changed.
        """
        value = self.__mainWidget.isChecked()
        self.valueChanged.emit(value)


OptionVisual.register('bool', BoolOptionVisual)
OptionVisual.registerFallbackDefaultVisual(bool, 'bool')

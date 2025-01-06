from Qt import QtWidgets
from .OptionVisual import OptionVisual


class FloatOptionVisual(OptionVisual):
    """
    Implement the widget for a float option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create FloatOptionVisual object.
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

        self.__mainWidget = QtWidgets.QDoubleSpinBox()
        self.__mainWidget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.__mainWidget.setMaximumWidth(150)
        self.__mainWidget.setRange(-99999999, 99999999)
        self.__mainWidget.setValue(float(self.optionValue()))
        self.__mainWidget.editingFinished.connect(self.__onValueChanged)

        mainLayout.addWidget(self.__mainWidget)

    def __onValueChanged(self):
        """
        Triggered when the spin box is changed.
        """
        value = self.__mainWidget.value()
        self.valueChanged.emit(value)


OptionVisual.register('float', FloatOptionVisual)
OptionVisual.registerFallbackDefaultVisual(float, 'float')

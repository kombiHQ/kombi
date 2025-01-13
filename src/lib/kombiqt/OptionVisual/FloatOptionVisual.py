import sys
from Qt import QtWidgets, QtCore
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
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        self.__mainWidget = QtWidgets.QDoubleSpinBox()
        self.__mainWidget.setRange(-sys.float_info.max, sys.float_info.max)
        self.__mainWidget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.__mainWidget.setMaximumWidth(self.uiHints().get('width', 100))
        mainLayout.addWidget(self.__mainWidget)

        self.__mainWidget.setValue(float(self.optionValue()))
        self.__mainWidget.editingFinished.connect(self.__onValueChanged)

        self.__sliderWidget = None
        if 'min' in self.uiHints() and 'max' in self.uiHints():
            self.__mainWidget.setRange(self.uiHints()['min'], self.uiHints()['max'])
            self.__sliderWidget = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.__sliderWidget.setTickPosition(QtWidgets.QSlider.TicksBothSides)
            self.__sliderWidget.setMinimum(self.uiHints()['min'])
            self.__sliderWidget.setMaximum(self.uiHints()['max'] * 1000)
            self.__sliderWidget.setValue(self.optionValue() * 1000)
            self.__sliderWidget.valueChanged.connect(self.__onSliderChanged)

            mainLayout.addWidget(self.__sliderWidget)
        else:
            mainLayout.addStretch(100)

    def __onSliderChanged(self, newValue):
        """
        Triggered when the slider is changed.
        """
        self.__mainWidget.setValue(newValue / 1000)
        self.__onValueChanged()

    def __onValueChanged(self):
        """
        Triggered when the spin box is changed.
        """
        value = self.__mainWidget.value()
        if self.__sliderWidget:
            self.__sliderWidget.setValue(value * 1000)
        self.valueChanged.emit(value)


OptionVisual.register('float', FloatOptionVisual)
OptionVisual.registerFallbackDefaultVisual('float', float)

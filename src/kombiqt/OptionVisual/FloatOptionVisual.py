import sys
from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual
from .IntOptionVisual import _Slider

class FloatOptionVisual(OptionVisual):
    """
    Implement the widget for a float option.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create FloatOptionVisual object.
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

        self.__mainWidget = _DoubleSpinBox()
        self.__mainWidget.setRange(-sys.float_info.max, sys.float_info.max)
        self.__mainWidget.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.__mainWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__mainWidget.setMaximumWidth(self.uiHints().get('width', 100))
        mainLayout.addWidget(self.__mainWidget)

        self.__mainWidget.setValue(float(self.optionValue()))

        # read only support
        if self.uiHints().get('readOnly', False):
            self.__mainWidget.setReadOnly(True)
            self.__mainWidget.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        else:
            self.__mainWidget.editingFinished.connect(self.__onValueChanged)

        self.__sliderWidget = None
        if 'min' in self.uiHints() and 'max' in self.uiHints() and self.uiHints().get('slider', True):
            self.__mainWidget.setRange(self.uiHints()['min'], self.uiHints()['max'])
            self.__sliderWidget = _Slider(QtCore.Qt.Horizontal)
            self.__sliderWidget.setTickPosition(QtWidgets.QSlider.NoTicks)
            self.__sliderWidget.setMinimum(self.uiHints()['min'])
            self.__sliderWidget.setMaximum(self.uiHints()['max'] * 1000)
            self.__sliderWidget.setValue(self.optionValue() * 1000)

            # read only
            if not self.uiHints().get('readOnly', False):
                # when "sliderUpdateOnTick" is enabled, whenever the slider is moved it will
                # update the value
                if self.uiHints().get('sliderUpdateOnTick', False):
                    self.__sliderWidget.valueChanged.connect(self.__onSliderChanged)
                # otherwise, only when the slider is released the value is updated
                else:
                    self.__sliderWidget.sliderReleased.connect(self.__onSliderChanged)
            else:
                self.__sliderWidget.setEnabled(False)

            mainLayout.addWidget(self.__sliderWidget)
        else:
            mainLayout.addStretch(100)

    def __onSliderChanged(self):
        """
        Triggered when the slider is changed.
        """
        newValue = self.__sliderWidget.value()
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


class _DoubleSpinBox(QtWidgets.QDoubleSpinBox):
    """
    Internal double spin box implementation necessary to disable the scrolling wheel.
    """

    def wheelEvent(self, event):
        """
        This is necessary to avoid the value being accidentally changed by scrolling the UI.
        """
        event.ignore()


# registering option visual
OptionVisual.register('float', FloatOptionVisual)
OptionVisual.registerFallbackDefaultVisual('float', float)

# registering examples
OptionVisual.registerExample('float', 'default', 0.1)
OptionVisual.registerExample('float', 'minMaxRange', 5.0, {'min': 3.0, 'max': 6.0})
OptionVisual.registerExample('float', 'minMaxRangeSlider', 5.0, {'min': 3.0, 'max': 6.0, 'slider': True})
OptionVisual.registerExample('float', 'minMaxRangeSliderUpdateValueOnTick', 5.0, {'min': 3.0, 'max': 6.0, 'slider': True, 'sliderUpdateOnTick': True})
OptionVisual.registerExample('float', 'minMaxRangeSliderReadOnly', 5.0, {'min': 3.0, 'max': 6.0, 'slider': True, 'readOnly': True})

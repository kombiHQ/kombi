from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual

class IntOptionVisual(OptionVisual):
    """
    Implement the widget for a float option.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create IntOptionVisual object.
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

        self.__mainWidget = _SpinBox()
        self.__mainWidget.setRange(-2147483647, 2147483647)
        self.__mainWidget.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.__mainWidget.setMaximumWidth(self.uiHints().get('width', 100))
        mainLayout.addWidget(self.__mainWidget)

        self.__mainWidget.setValue(int(self.optionValue()))
        self.__mainWidget.setFocusPolicy(QtCore.Qt.ClickFocus)

        # read only support
        if self.uiHints().get('readOnly', False):
            self.__mainWidget.setEnabled(False)
        else:
            self.__mainWidget.editingFinished.connect(self.__onValueChanged)

        self.__sliderWidget = None

        if 'min' in self.uiHints() and 'max' in self.uiHints() and self.uiHints().get('slider', True):
            self.__mainWidget.setRange(self.uiHints()['min'], self.uiHints()['max'])
            self.__sliderWidget = _Slider(QtCore.Qt.Horizontal)
            self.__sliderWidget.setTickPosition(QtWidgets.QSlider.NoTicks)
            self.__sliderWidget.setMinimum(self.uiHints()['min'])
            self.__sliderWidget.setMaximum(self.uiHints()['max'])
            self.__sliderWidget.setValue(self.optionValue())

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
        self.__mainWidget.setValue(newValue)
        self.__onValueChanged()

    def __onValueChanged(self):
        """
        Triggered when the spin box is changed.
        """
        value = self.__mainWidget.value()
        if self.__sliderWidget:
            self.__sliderWidget.setValue(value)
        self.valueChanged.emit(value)


class _SpinBox(QtWidgets.QSpinBox):
    """
    Internal spin box implementation necessary to disable the scrolling wheel.
    """

    def wheelEvent(self, event):
        """
        This is necessary to avoid the value being accidentally changed by scrolling the UI.
        """
        event.ignore()


class _Slider(QtWidgets.QSlider):
    """
    Internal slider implementation necessary to disable the scrolling wheel.
    """

    def wheelEvent(self, event):
        """
        This is necessary to avoid the value being accidentally changed by scrolling the UI.
        """
        event.ignore()


# registering option visual
OptionVisual.register('int', IntOptionVisual)
OptionVisual.registerFallbackDefaultVisual('int', int)

# registering examples
OptionVisual.registerExample('int', 'default', 2)
OptionVisual.registerExample('int', 'minMaxRange', 5, {'min': 3, 'max': 6})
OptionVisual.registerExample('int', 'minMaxRangeSlider', 5, {'min': 3, 'max': 6, 'slider': True})
OptionVisual.registerExample('int', 'minMaxRangeSliderUpdateValueOnTick', 5, {'min': 3, 'max': 6, 'slider': True, 'sliderUpdateOnTick': True})
OptionVisual.registerExample('int', 'minMaxRangeSliderReadOnly', 5, {'min': 3, 'max': 6, 'slider': True, 'readOnly': True})

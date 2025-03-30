from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual


class BoolOptionVisual(OptionVisual):
    """
    Implement the widget for a boolean option.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create BoolOptionVisual object.
        """
        super().__init__(optionValue, uiHints)

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

        # ready only support
        if self.uiHints().get('readOnly', False):
            self.__mainWidget.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        else:
            self.__mainWidget.stateChanged.connect(self.__onValueChanged)

        mainLayout.addWidget(self.__mainWidget)

    def __onValueChanged(self):
        """
        Triggered when the checkbox is changed.
        """
        value = self.__mainWidget.isChecked()
        self.valueChanged.emit(value)


# registering option visual
OptionVisual.register('bool', BoolOptionVisual)
OptionVisual.registerFallbackDefaultVisual('bool', bool)

# registering examples
OptionVisual.registerExample('bool', 'default', True)
OptionVisual.registerExample('bool', 'readOnly', True, {'readOnly': True})

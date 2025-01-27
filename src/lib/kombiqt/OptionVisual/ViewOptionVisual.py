from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual


class ViewOptionVisual(OptionVisual):
    """
    Implement a widget that only displays the value.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create ViewOptionVisual object.
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

        self.__mainWidget = QtWidgets.QLabel(str(self.optionValue()))
        self.__mainWidget.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        mainLayout.addWidget(self.__mainWidget)


# registering option visual
OptionVisual.register('view', ViewOptionVisual)

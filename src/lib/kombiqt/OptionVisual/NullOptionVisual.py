from Qt import QtWidgets
from .OptionVisual import OptionVisual


class NullOptionVisual(OptionVisual):
    """
    Implement the widget for a null option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create NullOptionVisual object.
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

        self.__mainWidget = QtWidgets.QLabel('NULL')
        mainLayout.addWidget(self.__mainWidget)


OptionVisual.register('null', NullOptionVisual)

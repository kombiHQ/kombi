from Qt import QtWidgets
from .OptionVisual import OptionVisual
from ..Element.ElementsLevelNavigationWidget import ElementsLevelNavigationWidget
from kombi.Element import Element

class ElementOptionVisual(OptionVisual):
    """
    Implement the widget for an element option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create ElementOptionVisual object.
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

        self.__mainWidget = ElementsLevelNavigationWidget(showBookmarks=False)
        self.__mainWidget.setElements([self.optionValue()])
        mainLayout.addWidget(self.__mainWidget)


OptionVisual.register('element', ElementOptionVisual)
OptionVisual.registerFallbackDefaultVisual('element', Element)

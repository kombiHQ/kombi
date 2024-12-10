import functools
from Qt import QtCore, QtWidgets
from kombi.Element import Element
from ..Resource import Resource

class ElementsLevelNavigationWidget(QtWidgets.QFrame):
    """
    Display the elements as individual buttons side by side.
    """
    levelClicked = QtCore.Signal(object)

    def __init__(self) -> None:
        """
        Create a ElementsLevelNavigationWidget object.
        """
        super(ElementsLevelNavigationWidget, self).__init__()
        self.setObjectName('elementsLevelNavigation')
        self.__elements = []
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.refresh()

    def refresh(self):
        """
        Refresh the render of levels displayed in the widget.
        """
        self.__deleteItemsOfLayout(self.layout())
        navigationLayout = QtWidgets.QHBoxLayout()
        navigationLayout.setSpacing(2)

        for element in self.__elements:
            elementNavigationButton = QtWidgets.QPushButton(element.var('name'))
            elementNavigationButton.setFlat(True)
            elementNavigationButton.clicked.connect(functools.partial(self.__onNavigationClicked, element))

            iconPath = element.tag('icon') if 'icon' in element.tagNames() else None
            if iconPath:
                elementNavigationButton.setIcon(
                    Resource.icon(iconPath)
                )

            navigationLayout.addWidget(elementNavigationButton, 10)
            if element != self.__elements[-1]:
                navigationLayout.addWidget(QtWidgets.QLabel('/'))

        navigationLayout.addStretch(1000)
        self.layout().addLayout(navigationLayout)

    def setElements(self, elements):
        """
        Set the elements that will be displayed in this widget.
        """
        for element in elements:
            assert isinstance(element, Element), "Invalid element type!"

        self.__elements = elements
        self.refresh()

    def elements(self):
        """
        Return the list of elements displayed by this widget.
        """
        return self.__elements

    def __onNavigationClicked(self, element):
        """
        Emit the level clicked signal.
        """
        self.levelClicked.emit(element)

    def __deleteItemsOfLayout(self, layout):
        """
        Utility method to remove all widgets in the layout.
        """
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                self.__deleteItemsOfLayout(item.layout())

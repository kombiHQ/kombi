from Qt import QtWidgets
from .OptionVisual import OptionVisual
from ..Widget.ElementListWidget import ElementListWidget

class ElementArrayOptionVisual(OptionVisual):
    """
    Implement a widget for an option with an array of elements.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create ElementArrayOptionVisual object.
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

        # creating a container for the element list widget
        frameLayout = QtWidgets.QHBoxLayout()
        frameLayout.setContentsMargins(0, 0, 0, 0)
        frameWidget = QtWidgets.QFrame()
        frameWidget.setObjectName('optionVisualContainer')
        frameWidget.setLayout(frameLayout)

        checkableState = self.uiHints().get('checkableState', False)
        elementVarColumnNames = self.uiHints().get('elementVarColumnNames', [])
        self.__mainWidget = ElementListWidget(
            checkableState=checkableState,
            elementVarColumnNames=elementVarColumnNames
        )

        # setting the minimumHeight ui hint when defined
        minimumHeight = self.uiHints().get('minimumHeight', 600)
        if minimumHeight:
            self.__mainWidget.setMinimumHeight(minimumHeight)

        if self.optionValue():
            self.__mainWidget.setElements(self.optionValue())

        self.__mainWidget.checkedStateChanged.connect(self.__onCheckedStateChanged)
        frameLayout.addWidget(self.__mainWidget)
        mainLayout.addWidget(frameWidget)

        # when checkable state is false we update the current value
        # to reflect an empty list
        if checkableState is False:
            self.valueChanged.emit([])

    def __onCheckedStateChanged(self):
        """
        Triggered when an item check state is changed.
        """
        elements = self.__mainWidget.checkedElements()
        self.valueChanged.emit(elements)


OptionVisual.register('elementArray', ElementArrayOptionVisual)
OptionVisual.registerExample('elementArray', 'checkboxOn', [], {'checkableState': True})
OptionVisual.registerExample('elementArray', 'checkboxOff', [], {'checkableState': False})
OptionVisual.registerExample('elementArray', 'columns', [], {'elementVarColumnNames': ['ext', 'type']})
OptionVisual.registerExample('elementArray', 'minimumHeight', [], {'minimumHeight': 500})

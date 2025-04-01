import functools
from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual
from ..Resource import Resource

class ArrayOptionVisual(OptionVisual):
    """
    Implement the widget for an array option.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create ArrayOptionVisual object.
        """
        super().__init__(optionValue, uiHints)
        self.__buildWidget()
        self.__refreshWidget()

    def _addEntries(self):
        """
        Return a list containing the values to be added.

        This method can be overridden by subclasses to implement custom behavior. If no
        entries are added, return an empty list instead.
        """
        return [self.uiHints().get('editableNewItemValue', '')]

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        self.__frameWidget = QtWidgets.QFrame()
        self.__frameWidget.setObjectName('optionVisualContainer')

        editable = self.uiHints().get('editable', False)
        if editable:
            scrollWidget = QtWidgets.QScrollArea()
            scrollWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            scrollWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            scrollWidget.setWidgetResizable(True)
            scrollWidget.setWidget(self.__frameWidget)
            scrollWidget.setMinimumHeight(self.uiHints().get('editableMinimumHeight', 100))
            mainLayout.addWidget(scrollWidget)
        else:
            mainLayout.addWidget(self.__frameWidget)

        if self.uiHints().get('orientation') == 'horizontal':
            contentLayout = QtWidgets.QHBoxLayout()
            contentLayout.setContentsMargins(4, 4, 4, 4)
        else:
            contentLayout = QtWidgets.QFormLayout()
            contentLayout.setLabelAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
            contentLayout.setContentsMargins(4, 4, 4, 4)

        self.__frameWidget.setLayout(contentLayout)

    def __refreshWidget(self):
        """
        Refresh the widget.
        """
        contentLayout = self.__frameWidget.layout()

        # cleaning current layout
        self.__deleteItemsOfLayout(contentLayout)

        itemsUiHints = self.uiHints().get('items', {})
        editable = self.uiHints().get('editable', False)
        for i, optionValue in enumerate(self.optionValue()):
            optionName = str(i)
            uiHints = itemsUiHints.get(optionName, {})
            itemWidget = OptionVisual.create(optionValue, uiHints)
            itemWidget.valueChanged.connect(functools.partial(self.__onItemValueChanged, i))

            if editable:
                rowLayout = QtWidgets.QHBoxLayout()
                rowLayout.setContentsMargins(0, 0, 0, 0)
                rowLayout.addWidget(itemWidget, 100)

                removeButton = QtWidgets.QPushButton()
                removeButton.setIcon(Resource.icon('icons/remove.png'))
                removeButton.setToolTip('Remove')
                removeButton.clicked.connect(functools.partial(self.__onRemove, i))
                rowLayout.addWidget(removeButton, 0)

                itemWidget = QtWidgets.QWidget()
                itemWidget.setLayout(rowLayout)

            label = uiHints.get('label', optionName)
            if isinstance(contentLayout, QtWidgets.QFormLayout):
                contentLayout.addRow(label, itemWidget)
            else:
                if i > 0:
                    contentLayout.addSpacing(20)
                contentLayout.addWidget(QtWidgets.QLabel(label))
                contentLayout.addWidget(itemWidget)

        if editable:
            addButton = QtWidgets.QPushButton('Add')
            addButton.setIcon(Resource.icon('icons/add.png'))
            addButton.clicked.connect(self.__onAdd)
            contentLayout.addWidget(addButton)

        if isinstance(contentLayout, QtWidgets.QHBoxLayout):
            contentLayout.addStretch(100)

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
                widget.deleteLater()
            else:
                self.__deleteItemsOfLayout(item.layout())

    def __onRemove(self, index):
        """
        Triggered when remove button is pressed.
        """
        value = list(self.optionValue())
        del value[index]
        self.valueChanged.emit(value)

        self.__refreshWidget()

    def __onAdd(self):
        """
        Triggered when add button is pressed.
        """
        value = list(self.optionValue())
        entries = self._addEntries()

        if not entries:
            return

        for entryValue in entries:
            value.append(entryValue)

        self.valueChanged.emit(value)

        self.__refreshWidget()

    def __onItemValueChanged(self, index, newValue):
        """
        Triggered when an item inside of the list is changed.
        """
        updatedValue = list(self.optionValue())
        updatedValue[index] = newValue

        self.valueChanged.emit(updatedValue)


# registering option visual
OptionVisual.register('array', ArrayOptionVisual)
OptionVisual.registerFallbackDefaultVisual('array', list)
OptionVisual.registerFallbackDefaultVisual('array', tuple)

# registering examples
OptionVisual.registerExample('array', 'default', ['a', 1, True, 'd'])
OptionVisual.registerExample('array', 'editable', ['a', 1, True, 'd'], {'editable': True})
OptionVisual.registerExample('array', 'editableNewItemValue', ['a', 1, True, 'd'], {'editable': True, 'editableNewItemValue': 0.0})
OptionVisual.registerExample('array', 'horizontal', ['a', 1, True, 'd'], {'orientation': 'horizontal'})
OptionVisual.registerExample(
    'array',
    'customItemLabel',
    ['a', 1, True, 'd'],
    {
        'items': {
            '1':  {
                'label': 'Custom Label for 1'
            },
            '3': {
                'label': 'Custom Label for 3'
            }
        }
    }
)

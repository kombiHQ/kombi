import functools
from fnmatch import fnmatch
from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual
from ..Resource import Resource


class HashmapOptionVisual(OptionVisual):
    """
    Implement the widget for a hashmap option.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create HashmapOptionVisual object.
        """
        super().__init__(optionValue, uiHints)

        self.__buildWidget()
        self.__refreshWidget()

    def _addEntries(self):
        """
        Return a dictionary containing the new keys and their corresponding values to be added.

        This method can be overridden by subclasses to implement custom behavior. If no
        entries are added, return an empty dictionary instead.
        """
        newItemName, ok = QtWidgets.QInputDialog.getText(self, 'Add', 'Enter key name:')
        newValue = self.uiHints().get('editableNewItemValue', '')

        if not ok or not newItemName:
            return {}

        if newItemName in self.optionValue():
            QtWidgets.QMessageBox.critical(self, 'Key error', f'Can\' add key "{newItemName}". It already exists!')
            return {}

        return {newItemName: newValue}

    def _removeEntry(self, key):
        """
        Return a boolean telling if the key can be deleted.

        This method can be overridden by subclasses to implement custom behavior (like
        a confirmation).
        """
        return True

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
        i = 0
        for optionName, optionValue in self.optionValue().items():
            uiHints = {}
            # when there is a UI hint specifically defined
            # for the item option name
            if optionName in itemsUiHints:
                uiHints = itemsUiHints[optionName]
            else:
                # try to look for the UI Hint using fnmatch
                for itemName, itemUiHints in itemsUiHints.items():
                    if fnmatch(optionName, itemName):
                        uiHints = itemUiHints
                        break

            # in case the hidden metadata is defined we don't render it
            if uiHints.get('hidden', False):
                continue

            itemWidget = OptionVisual.create(optionValue, uiHints)
            itemWidget.valueChanged.connect(functools.partial(self.__onItemValueChanged, optionName))

            if editable:
                rowLayout = QtWidgets.QHBoxLayout()
                rowLayout.setContentsMargins(0, 0, 0, 0)
                rowLayout.addWidget(itemWidget, 100)

                removeButton = QtWidgets.QPushButton()
                removeButton.setIcon(Resource.icon('icons/remove.png'))
                removeButton.setToolTip('Remove')
                removeButton.clicked.connect(functools.partial(self.__onRemove, optionName))
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
            i += 1

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

    def __onRemove(self, key):
        """
        Triggered when remove button is pressed.
        """
        if not self._removeEntry(key):
            return

        value = dict(self.optionValue())
        del value[key]
        self.valueChanged.emit(value)

        self.__refreshWidget()

    def __onAdd(self):
        """
        Triggered when add button is pressed.
        """
        value = dict(self.optionValue())
        entries = self._addEntries()

        if not entries:
            return

        for newEntryKey, newEntryValue in entries.items():
            value[newEntryKey] = newEntryValue

        self.valueChanged.emit(value)

        self.__refreshWidget()

    def __onItemValueChanged(self, optionName, newValue):
        """
        Triggered when an item inside of the dict is changed.
        """
        updatedValue = dict(self.optionValue())
        updatedValue[optionName] = newValue

        self.valueChanged.emit(updatedValue)


# registering option visual
OptionVisual.register('hashmap', HashmapOptionVisual)
OptionVisual.registerFallbackDefaultVisual('hashmap', dict)

# registering examples
OptionVisual.registerExample('hashmap', 'default', {'a': 'a', 'b': 1, 'c': True, 'd': 'd'})
OptionVisual.registerExample('hashmap', 'editable', {'a': 1, 'b': 'd'}, {'editable': True})
OptionVisual.registerExample('hashmap', 'editableNewItemValue', {'a': 1, 'b': 'd'}, {'editable': True, 'editableNewItemValue': 0.0})
OptionVisual.registerExample('hashmap', 'horizontal', {'a': 'a', 'b': 1, 'c': True, 'd': 'd'}, {'orientation': 'horizontal'})
OptionVisual.registerExample(
    'hashmap',
    'customItemLabel',
    {'a': 'a', 'b': 1, 'c': True, 'd': 'd'},
    {
        'items': {
            'b':  {
                'label': 'Custom Label for b'
            },
            'd': {
                'label': 'Custom Label for d'
            }
        }
    }
)

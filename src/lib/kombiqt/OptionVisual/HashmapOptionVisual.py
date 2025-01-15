import functools
from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual


class HashmapOptionVisual(OptionVisual):
    """
    Implement the widget for a hashmap option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create HashmapOptionVisual object.
        """
        super().__init__(optionName, optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        if self.uiHints().get('orientation') == 'horizontal':
            contentLayout = QtWidgets.QHBoxLayout()
            contentLayout.setContentsMargins(4, 4, 4, 4)
        else:
            contentLayout = QtWidgets.QFormLayout()
            contentLayout.setLabelAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
            contentLayout.setContentsMargins(4, 4, 4, 4)

        itemsUiHints = self.uiHints().get('items', {})
        i = 0
        for optionName, optionValue in self.optionValue().items():
            uiHints = itemsUiHints.get(optionName, {})
            itemWidget = OptionVisual.create(optionName, optionValue, uiHints)
            itemWidget.valueChanged.connect(functools.partial(self.__onItemValueChanged, optionName))

            label = uiHints.get('label', optionName)
            if isinstance(contentLayout, QtWidgets.QFormLayout):
                contentLayout.addRow(label, itemWidget)
            else:
                if i > 0:
                    contentLayout.addSpacing(20)
                contentLayout.addWidget(QtWidgets.QLabel(label))
                contentLayout.addWidget(itemWidget)
            i += 1

        if isinstance(contentLayout, QtWidgets.QHBoxLayout):
            contentLayout.addStretch(100)

        frameWidget = QtWidgets.QFrame()
        frameWidget.setObjectName('optionVisualContainer')
        frameWidget.setLayout(contentLayout)

        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        mainLayout.addWidget(frameWidget)
        self.setLayout(mainLayout)

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

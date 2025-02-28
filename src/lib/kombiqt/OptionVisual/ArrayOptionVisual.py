import functools
from Qt import QtWidgets, QtCore
from .OptionVisual import OptionVisual


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
        for i, optionValue in enumerate(self.optionValue()):
            optionName = str(i)
            uiHints = itemsUiHints.get(optionName, {})
            itemWidget = OptionVisual.create(optionValue, uiHints)
            itemWidget.valueChanged.connect(functools.partial(self.__onItemValueChanged, i))

            label = uiHints.get('label', optionName)
            if isinstance(contentLayout, QtWidgets.QFormLayout):
                contentLayout.addRow(label, itemWidget)
            else:
                if i > 0:
                    contentLayout.addSpacing(20)
                contentLayout.addWidget(QtWidgets.QLabel(label))
                contentLayout.addWidget(itemWidget)

        if isinstance(contentLayout, QtWidgets.QHBoxLayout):
            contentLayout.addStretch(100)

        frameWidget = QtWidgets.QFrame()
        frameWidget.setObjectName('optionVisualContainer')
        frameWidget.setLayout(contentLayout)

        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        mainLayout.addWidget(frameWidget)
        self.setLayout(mainLayout)

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

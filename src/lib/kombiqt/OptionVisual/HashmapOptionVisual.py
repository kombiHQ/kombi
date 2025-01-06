import functools
from Qt import QtWidgets
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
        formLayout = QtWidgets.QFormLayout()
        formLayout.setContentsMargins(4, 4, 4, 4)

        itemsUiHints = self.uiHints().get('items', {})
        for optionName, optionValue in self.optionValue().items():
            uiHints = itemsUiHints.get(optionName, {})
            itemWidget = OptionVisual.create(optionName, optionValue, uiHints)
            itemWidget.valueChanged.connect(functools.partial(self.__onItemValueChanged, optionName))
            formLayout.addRow(uiHints.get('label', optionName), itemWidget)

        frameWidget = QtWidgets.QFrame()
        frameWidget.setObjectName('optionVisualContainer')
        frameWidget.setLayout(formLayout)

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


OptionVisual.register('hashmap', HashmapOptionVisual)
OptionVisual.registerFallbackDefaultVisual('hashmap', dict)

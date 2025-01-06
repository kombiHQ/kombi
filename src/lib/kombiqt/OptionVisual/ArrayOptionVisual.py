import functools
from Qt import QtWidgets
from .OptionVisual import OptionVisual


class ArrayOptionVisual(OptionVisual):
    """
    Implement the widget for an array option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create ArrayOptionVisual object.
        """
        super().__init__(optionName, optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QFormLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        itemsUiHints = self.uiHints().get('items', {})
        for i, optionValue in enumerate(self.optionValue()):
            optionName = str(i)
            uiHints = itemsUiHints.get(optionName, {})
            itemWidget = OptionVisual.create(optionName, optionValue, uiHints)
            itemWidget.valueChanged.connect(functools.partial(self.__onItemValueChanged, i))
            mainLayout.addRow(optionName, itemWidget)

    def __onItemValueChanged(self, index, newValue):
        """
        Triggered when an item inside of the list is changed.
        """
        updatedValue = list(self.optionValue())
        updatedValue[index] = newValue

        self.valueChanged.emit(updatedValue)


OptionVisual.register('array', ArrayOptionVisual)
OptionVisual.registerFallbackDefaultVisual('array', list)
OptionVisual.registerFallbackDefaultVisual('array', tuple)

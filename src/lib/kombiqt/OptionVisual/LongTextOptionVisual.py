from Qt import QtWidgets
from .OptionVisual import OptionVisual


class LongTextOptionVisual(OptionVisual):
    """
    Implement the widget for a long text option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create LongTextOptionVisual object.
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

        self.__mainWidget = QtWidgets.QTextEdit(self)
        self.__mainWidget.setMinimumHeight(100)
        self.__mainWidget.setMaximumHeight(100)
        self.__mainWidget.setPlainText(str(self.optionValue()))
        self.__mainWidget.textChanged.connect(self.__onValueChanged)

        mainLayout.addWidget(self.__mainWidget)

    def __onValueChanged(self):
        """
        Triggered when the text field is changed.
        """
        value = self.__mainWidget.toPlainText()
        self.valueChanged.emit(value)


OptionVisual.register('longText', LongTextOptionVisual)

from Qt import QtWidgets, QtGui
from .OptionVisual import OptionVisual


class TextOptionVisual(OptionVisual):
    """
    Implement the widget for a text option.
    """

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create TextOptionVisual object.
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

        self.__mainWidget = QtWidgets.QLineEdit(str(self.optionValue()))

        if 'regex' in self.uiHints():
            self.__mainWidget.setValidator(QtGui.QRegExpValidator(self.uiHints()['regex']))

        if 'caseStyle' in self.uiHints():
            self.__mainWidget.textEdited.connect(self.__onToCase)

        self.__mainWidget.textEdited.connect(self.__onValueChanged)
        mainLayout.addWidget(self.__mainWidget)

    def __onToCase(self, text):
        """
        Triggered when the text is changed to apply the case style.
        """
        case = self.uiHints().get('caseStyle')
        self.__mainWidget.setText(text.upper() if case == 'uppercase' else text.lower())

    def __onValueChanged(self):
        """
        Triggered when the text field is changed.
        """
        value = self.__mainWidget.text()
        self.valueChanged.emit(value)


OptionVisual.register('text', TextOptionVisual)
OptionVisual.registerFallbackDefaultVisual('text', str)

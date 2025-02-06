from Qt import QtWidgets, QtGui,  QtCore
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
        self.__pendingTextEdited = False
        self.__buildWidget()

    def event(self, event):
        """
        Necessary to handle edited text only when the user leaves the widget to avoid unnecessary processing.
        """
        if event.type() == QtCore.QEvent.Type.Leave and self.__pendingTextEdited:
            self.__pendingTextEdited = False
            self.__onValueChanged()

        return super().event(event)

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        self.__mainWidget = QtWidgets.QLineEdit(str(self.optionValue()))
        self.__mainWidget.setReadOnly(self.uiHints().get('readOnly', False))

        if 'regex' in self.uiHints():
            self.__mainWidget.setValidator(QtGui.QRegExpValidator(self.uiHints()['regex']))

        self.__mainWidget.textEdited.connect(self.__onToCase)

        # this signal is unreliable, emitted only when the widget loses focus or the
        # enter key is pressed. Therefore, we combine it with a QEvent.Type.Leave to
        # ensure reliable propagation.
        self.__mainWidget.editingFinished.connect(self.__onValueChanged)
        mainLayout.addWidget(self.__mainWidget)

    def __onToCase(self, text):
        """
        Triggered when the text is changed to apply the case style.
        """
        case = self.uiHints().get('caseStyle', None)
        if case is not None:
            currentPosition = self.__mainWidget.cursorPosition()
            self.__mainWidget.setText(text.upper() if case == 'uppercase' else text.lower())
            self.__mainWidget.setCursorPosition(currentPosition)
        self.__pendingTextEdited = True

    def __onValueChanged(self):
        """
        Triggered when the text field is changed.
        """
        value = self.__mainWidget.text()

        if self.optionValue() == value:
            return

        self.valueChanged.emit(value)


# registering option visual
OptionVisual.register('text', TextOptionVisual)
OptionVisual.registerFallbackDefaultVisual('text', str)

# registering examples
OptionVisual.registerExample('text', 'default', 'Text')
OptionVisual.registerExample('text', 'regex', 'NoSpecialCharactersAreAllowed', {'regex': '^[A-Za-z0-9]*'})
OptionVisual.registerExample('text', 'caseStyleUppercase', 'FORCE UPPER CASE', {'caseStyle': 'uppercase'})
OptionVisual.registerExample('text', 'caseStyleLowercase', 'force lower case', {'caseStyle': 'lowercase'})

from Qt import QtWidgets, QtGui, QtCore
from .OptionVisual import OptionVisual


class HexColorOptionVisual(OptionVisual):
    """
    Implement the widget for a hex color option.
    """

    def __init__(self, optionValue, uiHints=None):
        """
        Create HexColorOptionVisual object.
        """
        super().__init__(optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QHBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(mainLayout)

        self.__mainWidget = QtWidgets.QLineEdit(str(self.optionValue()))
        self.__mainWidget.textEdited.connect(self.__onValueChanged)
        self.__mainWidget.setMaximumWidth(self.uiHints().get('width', 100))

        self.__currentColorButton = QtWidgets.QPushButton()
        self.__currentColorButton.setFixedWidth(30)
        self.__currentColorButton.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__currentColorButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.__currentColorButton.clicked.connect(self.__onOpenChangeColor)
        self.__currentColorButton.setToolTip('Click to change color')

        mainLayout.addWidget(self.__mainWidget)
        mainLayout.addWidget(self.__currentColorButton)
        mainLayout.addStretch()
        self.__updateCurrentColorFrame()

    def __onOpenChangeColor(self):
        """
        Triggered when the change color button is pressed.
        """
        currentColor = QtGui.QColor(self.__mainWidget.text())
        color = QtWidgets.QColorDialog.getColor(
            currentColor,
            self,
            "Pick Color",
            QtWidgets.QColorDialog.DontUseNativeDialog
        )
        if not color.isValid():
            return

        hexColor = color.name()
        self.__mainWidget.setText(hexColor)
        self.__onValueChanged()

    def __updateCurrentColorFrame(self):
        """
        Update the background color displayed at the current color frame.
        """
        currentColor = self.__mainWidget.text()
        if not QtGui.QColor(currentColor).isValid():
            currentColor = "#00000000"

        self.__currentColorButton.setStyleSheet("background-color: {}; border: 1px groove #333333".format(currentColor))

    def __onValueChanged(self):
        """
        Triggered when the text field is changed.
        """
        self.__updateCurrentColorFrame()
        value = self.__mainWidget.text()
        self.valueChanged.emit(value)


# registering option visual
OptionVisual.register('hexcolor', HexColorOptionVisual)

# registering examples
OptionVisual.registerExample('hexcolor', 'default', '#0000FF')

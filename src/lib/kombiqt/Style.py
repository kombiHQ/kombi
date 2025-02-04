from Qt import QtCore, QtGui, QtWidgets
from .Resource import Resource

class Style(object):
    """
    Kombi style.
    """

    @classmethod
    def apply(cls, widget, style=True, font=True, palette=True, styleSheet=True):
        """
        Apply the default stylesheet to the interface.
        """
        if style:
            widget.setStyle(QtWidgets.QStyleFactory.create('Fusion'))

        if font:
            cls.__applyFont(widget)

        if palette:
            cls.__applyPalette(widget)

        if styleSheet:
            widget.setStyleSheet(
                Resource.stylesheet()
            )

    @classmethod
    def __applyFont(cls, widget):
        """
        Apply the default font.
        """
        defaultFont = QtGui.QFont(Resource.fontName())
        defaultFont.setPointSize(Resource.fontSize())
        widget.setFont(defaultFont)

    @classmethod
    def __applyPalette(cls, widget):
        """
        Apply the palette to the widget.
        """
        darkPalette = QtGui.QPalette()

        darkPalette.setColor(
            QtGui.QPalette.Window,
            QtGui.QColor(53, 53, 53)
        )

        darkPalette.setColor(
            QtGui.QPalette.WindowText,
            QtCore.Qt.white
        )

        darkPalette.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.WindowText,
            QtGui.QColor(127, 127, 127)
        )

        darkPalette.setColor(
            QtGui.QPalette.Base,
            QtGui.QColor(42, 42, 42)
        )

        darkPalette.setColor(
            QtGui.QPalette.AlternateBase,
            QtGui.QColor(66, 66, 66)
        )

        darkPalette.setColor(
            QtGui.QPalette.ToolTipBase,
            QtGui.QColor(230, 230, 230)
        )

        darkPalette.setColor(
            QtGui.QPalette.ToolTipText,
            QtGui.QColor(230, 230, 230)
        )

        darkPalette.setColor(
            QtGui.QPalette.Text,
            QtGui.QColor(230, 230, 230)
        )

        darkPalette.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.Text,
            QtGui.QColor(127, 127, 127)
        )

        darkPalette.setColor(
            QtGui.QPalette.Dark,
            QtGui.QColor(35, 35, 35)
        )

        darkPalette.setColor(
            QtGui.QPalette.Shadow,
            QtGui.QColor(20, 20, 20)
        )

        darkPalette.setColor(
            QtGui.QPalette.Button,
            QtGui.QColor(53, 53, 53)
        )

        darkPalette.setColor(
            QtGui.QPalette.ButtonText,
            QtGui.QColor(230, 230, 230)
        )

        darkPalette.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.ButtonText,
            QtGui.QColor(127, 127, 127)
        )

        darkPalette.setColor(
            QtGui.QPalette.BrightText,
            QtCore.Qt.red
        )

        darkPalette.setColor(
            QtGui.QPalette.Link,
            QtGui.QColor(42, 130, 218)
        )

        darkPalette.setColor(
            QtGui.QPalette.Highlight,
            QtGui.QColor(42, 130, 218)
        )

        darkPalette.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.Highlight,
            QtGui.QColor(80, 80, 80)
        )

        darkPalette.setColor(
            QtGui.QPalette.HighlightedText,
            QtCore.Qt.white
        )

        darkPalette.setColor(
            QtGui.QPalette.Disabled,
            QtGui.QPalette.HighlightedText,
            QtGui.QColor(127, 127, 127)
        )

        widget.setPalette(darkPalette)

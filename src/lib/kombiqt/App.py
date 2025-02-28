from Qt import QtWidgets, QtCore
from .Style import Style

class App(QtWidgets.QApplication):
    """
    Implementation of QApplication used by kombi.
    """

    def __init__(self, argv, **kwargs):
        """
        Create a Kombi app.
        """
        super(App, self).__init__(argv, **kwargs)

        # disabling dpi scaling to prevent inconsistent font rendering
        self.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling, True)
        self.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, False)

        Style.apply(self)

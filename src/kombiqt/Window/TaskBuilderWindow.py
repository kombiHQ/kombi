from Qt import QtWidgets, QtCore
from ..Widget.PythonTextEditWidget import PythonTextEditWidget
from ..Resource import Resource

class TaskBuilderWindow(QtWidgets.QMainWindow):
    """
    Kombi task builder window.
    """

    def __init__(self, parent=None):
        """
        Create TaskBuilderWindow object.
        """
        super().__init__(parent=parent)
        self.setWindowTitle('Kombi Task Builder')
        self.setWindowIcon(Resource.icon('icons/kombi.png'))
        self.setStyleSheet(Resource.stylesheet())

        self.__buildWidgets()

    def __buildWidgets(self):
        """
        Build the base widgets.
        """
        mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(mainLayout)
        mainLayout.addWidget(QtWidgets.QPushButton('test'))
        mainLayout.addWidget(PythonTextEditWidget())

        # readOnly?
        # required
        # main
        # separator

        # custom label
        # custom tooltip

        # add a way to specify a header image/text (like the main UI, driven by metatada)
        # split it as separated widget...

        Custom Label: [         ]
        Custom Tooltip: [         ]

        visual examples: [         |v]
        Value: [              ]

        [x] required
        [ ] main
        [ ] readOnly
        [x] separator
        [ ] hidden

        boiler plate output in python, json, toml yaml





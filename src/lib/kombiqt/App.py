import os
import sys
from Qt import QtWidgets, QtCore
from kombi.Element.Fs.FsElement import FsElement
from kombi.Element import Element
from .Window.MainWindow import MainWindow
from .Resource import Resource
from .Style import Style

class App(QtWidgets.QApplication):
    """
    Basic graphical interface to pick files to run through a kombi configuration.

    Deprecation Notice: This interface is going to be phase out in future releases.

    Example:
        kombi-gui <CONFIGURATION-DIRECTORY> [<INPUT-FILES-DIRECTORY>]
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

        # getting configuration directory from the args
        configurationDirectory = ''
        if len(argv) > 1:
            configurationDirectory = argv[1]

        # otherwise from the environment
        elif 'KOMBIAPP_CONFIG_DIR' in os.environ:
            configurationDirectory = os.environ['KOMBIAPP_CONFIG_DIR']

        # showing configuration directory picker
        if not configurationDirectory:
            configurationDirectory = MainWindow.pickConfigurationDirectory(configurationDirectory)

        # loading task holders
        taskHolders = MainWindow.loadConfigurationTaskHolders(configurationDirectory)

        # source element path
        rootElement = None
        if len(sys.argv) > 2:
            rootElement = FsElement.createFromPath(sys.argv[2])
            # wrapping the leaf element a collection element, so it can be
            # displayed in the UI
            if rootElement.isLeaf():
                rootElement = Element.create([rootElement])

        self.__mainWindow = MainWindow(taskHolders, rootElement)
        self.__mainWindow.setWindowIcon(Resource.icon('icons/kombi.png'))
        self.__mainWindow.show()
        self.__mainWindow.activateWindow()

import os
import sys
from Qt import QtWidgets
from .Window.RunnerWindow import RunnerWindow
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
            configurationDirectory = RunnerWindow.pickConfigurationDirectory(configurationDirectory)

        # loading task holders
        taskHolders = RunnerWindow.loadConfigurationTaskHolders(configurationDirectory)

        # source element paths
        sourcePaths = []
        if len(sys.argv) > 2:
            sourcePaths = sys.argv[2:]

        self.__mainWindow = RunnerWindow(taskHolders, sourcePaths)
        self.__mainWindow.setWindowIcon(Resource.icon('icons/kombi.png'))
        self.__mainWindow.show()
        self.__mainWindow.activateWindow()

import os
import pathlib
import mimetypes
from Qt import QtWidgets, QtCore
from ..Resource import Resource
from ..OptionVisual.PathBrowserOptionVisual import PathBrowserOptionVisual
from ..Widget.ScriptEditorTabWidget import ScriptEditorTabWidget

class ScriptEditorWindow(QtWidgets.QMainWindow):
    """
    Kombi script editor window.
    """

    def __init__(self, rootPath='', mainWidget=None, parent=None):
        """
        Create ScriptEditorWindow object.
        """
        super().__init__(parent=parent)
        self.setWindowTitle('Kombi Script Editor')
        self.setWindowIcon(Resource.icon('icons/kombi.png'))
        self.setStyleSheet(Resource.stylesheet())

        self.__buildWidgets(mainWidget)

        if mainWidget is None:
            self.__createFileBrowserWidget(rootPath)

        self.resize(1280, 720)

    def mainWidget(self):
        """
        Return the main widget associated with the window, or None if it's not defined.
        """
        return self.__scriptEditorTabWidget.mainWidget()

    def tabWidget(self):
        """
        Return the script editor tab widget.
        """
        return self.__scriptEditorTabWidget

    def __buildWidgets(self, mainWidget):
        """
        Build the base widgets.
        """
        self.__horizontalSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.__scriptEditorTabWidget = ScriptEditorTabWidget(mainWidget=mainWidget)
        self.__horizontalSplitter.addWidget(self.__scriptEditorTabWidget)

        self.setCentralWidget(self.__horizontalSplitter)

    def keyPressEvent(self, event):
        """
        Handle showing the file browser hotkey.
        """
        # F1: show tree
        if event.key() == QtCore.Qt.Key_F1:
            if self.__horizontalSplitter.count() == 1:
                self.__createFileBrowserWidget()
            else:
                browserWidget = self.__horizontalSplitter.widget(0)
                browserWidget.setVisible(not browserWidget.isVisible())

        super().keyPressEvent(event)

    def __createFileBrowserWidget(self, rootPath=''):
        """
        The file browser widget is created on demand only when requested.
        """
        if not rootPath:
            rootPath = Resource.userConfig().value('scriptEditorRootPath', pathlib.Path.home().as_posix())

        self.__scriptEditorFileBrowser = PathBrowserOptionVisual(
            'scriptEditor',
            '',
            {
                'rootPath': rootPath,
                'showColumns': False
            }
        )

        self.__scriptEditorFileBrowser.rootChanged.connect(self.__onScriptEditorFileBrowserRootChanged)
        self.__scriptEditorFileBrowser.doubleClick.connect(self.__onScriptEditorDoubleClick)
        self.__horizontalSplitter.insertWidget(0, self.__scriptEditorFileBrowser)
        self.__horizontalSplitter.setSizes((200, 600))
        self.__horizontalSplitter.setStretchFactor(0, 0)
        self.__horizontalSplitter.setStretchFactor(1, 1)

    def __onScriptEditorFileBrowserRootChanged(self, rootPath):
        """
        Triggered when the root path is changed in the script editor file browser.
        """
        Resource.userConfig().setValue('scriptEditorRootPath', rootPath)

    def __onScriptEditorDoubleClick(self):
        """
        Triggered when an item is double clicked inside of the script editor file browser.
        """
        filePath = self.__scriptEditorFileBrowser.optionValue()
        if not filePath:
            return

        mimeType = mimetypes.guess_type(filePath)[0]
        if mimeType and mimeType.startswith('text/'):
            baseName = os.path.basename(filePath)
            self.__scriptEditorTabWidget.addScriptEditor(filePath=filePath, tabName=baseName)

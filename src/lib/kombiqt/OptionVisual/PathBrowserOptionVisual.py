import pathlib
from kombi.Task import Task
from kombi.Element.Fs.FsElement import FsElement
from Qt import QtWidgets, QtCore, QtGui
from .OptionVisual import OptionVisual
from .DirectoryPathOptionVisual import DirectoryPathOptionVisual
from ..Resource import Resource


class PathBrowserOptionVisual(OptionVisual):
    """
    Implement the widget for an option visual list shows a browser.
    """
    doubleClick = QtCore.Signal()
    rootChanged = QtCore.Signal(str)

    def __init__(self, optionValue, uiHints=None):
        """
        Create PathBrowserOptionVisual object.
        """
        super().__init__(optionValue, uiHints)

        self.__buildWidget()

    def __buildWidget(self):
        """
        Implement the widget.
        """
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setContentsMargins(2, 2, 2, 2)
        mainLayout.setSpacing(0)
        self.setLayout(mainLayout)

        rootPath = self.uiHints().get('rootPath', '').replace('\\', '/')
        self.__rootWidget = DirectoryPathOptionVisual(
            rootPath,
            {
                'label': self.uiHints().get('rootButtonLabel', '')
            }
        )
        self.__rootWidget.valueChanged.connect(self.__onRootChanged)
        self.__fileSystemModel = _FileSystemModel(displayIcons=self.uiHints().get('displayIcons', True))
        self.__fileSystemModel.setRootPath(self.__rootWidget.optionValue())

        self.__treeWidget = _TreeView()
        self.__treeWidget.contextMenu.connect(self.__onContextMenu)
        self.__treeWidget.setTextElideMode(QtCore.Qt.ElideNone)
        self.__treeWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.__treeWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.__treeWidget.setModel(self.__fileSystemModel)

        if not self.uiHints().get('showColumns', True):
            self.__treeWidget.setHeaderHidden(True)
            for column in range(1, self.__fileSystemModel.columnCount()):
                self.__treeWidget.setColumnHidden(column, True)

        self.__onRootChanged(self.__rootWidget.optionValue())
        self.__treeWidget.setUniformRowHeights(True)
        self.__treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.__treeWidget.doubleClicked.connect(self.__onDoubleClick)
        self.__treeWidget.selectionModel().selectionChanged.connect(self.__onSelectionChanged)
        self.__treeWidget.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        mainLayout.addWidget(self.__rootWidget)
        mainLayout.addWidget(self.__treeWidget)

    def __onContextMenu(self, event):
        """
        Implement a context menu for the selected item in the tree.
        """
        contextMenu = QtWidgets.QMenu(self)

        revealInFileManagerAction = QtWidgets.QAction("Reveal in file manager", self)
        revealInFileManagerAction.triggered.connect(self.__onRevealInFileManager)
        contextMenu.addAction(revealInFileManagerAction)

        launchWithDefaultApplicationAction = QtWidgets.QAction("Open with default application", self)
        launchWithDefaultApplicationAction.triggered.connect(self.__onLaunchWithDefaultApplication)
        contextMenu.addAction(launchWithDefaultApplicationAction)

        if self.uiHints().get('showCreateDirectory', True) and pathlib.Path(self.optionValue()).is_dir():
            createSubDirectoryAction = QtWidgets.QAction("Create Sub-Directory", self)
            createSubDirectoryAction.triggered.connect(self.__onCreateSubDirectory)
            contextMenu.addAction(createSubDirectoryAction)

        contextMenu.exec_(event.globalPos())

    def __onRevealInFileManager(self):
        """
        Triggered when the action "Reveal in File manager" is selected.
        """
        task = Task.create('revealInFileManager')
        task.add(FsElement.createFromPath(self.optionValue()))
        task.output()

    def __onLaunchWithDefaultApplication(self):
        """
        Triggered when the action "Launch with default application" is selected.
        """
        task = Task.create('launchWithDefaultApplication')
        task.add(FsElement.createFromPath(self.optionValue()))
        task.output()

    def __onCreateSubDirectory(self):
        """
        Triggered when the action "Create sub-directory" is selected.
        """
        currentDirectory = pathlib.Path(self.optionValue())
        newDirectoryName, ok = QtWidgets.QInputDialog.getText(
            self,
            f"Create sub-directory under {currentDirectory.name}:",
            "Enter directory name:",
            text=""
        )
        if ok and newDirectoryName:
            currentDirectory.joinpath(newDirectoryName).mkdir()

    def __onRootChanged(self, location):
        """
        Triggered when root path is changed.
        """
        self.__fileSystemModel.setRootPath(location)
        self.__treeWidget.setRootIndex(self.__fileSystemModel.index(location))
        self.rootChanged.emit(location)

    def __onSelectionChanged(self, *_):
        """
        Triggered when an item is selected in the tree.
        """
        selectedIndexes = self.__treeWidget.selectionModel().selectedIndexes()
        newPath = ''
        if selectedIndexes:
            newPath = self.__fileSystemModel.filePath(selectedIndexes[0])
        self.valueChanged.emit(newPath)

    def __onDoubleClick(self, _):
        """
        Triggered when an user double click in a file/directory in the browser.
        """
        self.doubleClick.emit()

class _TreeView(QtWidgets.QTreeView):
    """
    Custom QTreeView subclass that emits a signal when the context menu event is triggered.
    """
    contextMenu = QtCore.Signal(object)

    def contextMenuEvent(self, event):
        """
        Override the default context menu event to emit the contextMenu signal.
        """
        self.contextMenu.emit(event)

class _FileSystemModel(QtWidgets.QFileSystemModel):
    """
    File system model used by the tree widget.
    """
    __nullPixmap = None

    def __init__(self, displayIcons=True):
        """
        Create _FileSystemModel object.
        """
        super().__init__()
        self.__setDisplayIcons(displayIcons)

    def data(self, index, role):
        """
        Return the model data.
        """
        if not self.displayIcons() and role == QtCore.Qt.DecorationRole and index.column() == 0:
            if self.__nullPixmap is None:
                self.__nullPixmap = QtGui.QPixmap()

            return self.__nullPixmap

        if role == QtCore.Qt.DecorationRole and index.column() == 0 and self.isDir(index):
            return Resource.icon('icons/elements/children.png')
        return super().data(index, role)

    def displayIcons(self):
        """
        Return a boolean telling if the icons are being display.
        """
        return self.__displayIcons

    def __setDisplayIcons(self, value):
        """
        Set a boolean telling if the model should display the icons.
        """
        self.__displayIcons = value


# registering option visual
OptionVisual.register('pathBrowser', PathBrowserOptionVisual)

# registering examples
OptionVisual.registerExample('pathBrowser', 'rootPath', '', {'rootPath': pathlib.Path.home().as_posix()})
OptionVisual.registerExample('pathBrowser', 'hideColumns', '', {'rootPath': pathlib.Path.home().as_posix(), 'showColumns': False})
OptionVisual.registerExample('pathBrowser', 'rootButtonLabel', '', {'rootPath': pathlib.Path.home().as_posix(), 'rootButtonLabel': 'Custom Label'})
OptionVisual.registerExample('pathBrowser', 'hideIcons', '', {'rootPath': pathlib.Path.home().as_posix(), 'displayIcons': False})

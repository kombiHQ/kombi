import pathlib
from Qt import QtWidgets, QtCore
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
        self.__fileSystemModel = _FileSystemModel()
        self.__fileSystemModel.setRootPath(self.__rootWidget.optionValue())

        self.__treeWidget = QtWidgets.QTreeView()
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

class _FileSystemModel(QtWidgets.QFileSystemModel):
    """
    File system model used by the tree widget.
    """
    def data(self, index, role):
        if role == QtCore.Qt.DecorationRole and index.column() == 0 and self.isDir(index):
            return Resource.icon('icons/elements/children.png')
        return super().data(index, role)


# registering option visual
OptionVisual.register('pathBrowser', PathBrowserOptionVisual)

# registering examples
OptionVisual.registerExample('pathBrowser', 'rootPath', '', {'rootPath': pathlib.Path.home().as_posix()})
OptionVisual.registerExample('pathBrowser', 'hideColumns', '', {'rootPath': pathlib.Path.home().as_posix(), 'showColumns': False})
OptionVisual.registerExample('pathBrowser', 'rootButtonLabel', '', {'rootPath': pathlib.Path.home().as_posix(), 'rootButtonLabel': 'Custom Label'})

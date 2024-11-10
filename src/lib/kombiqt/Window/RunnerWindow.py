import os
import re
import json
import getpass
import datetime
import traceback
import platform
import functools
import hashlib
import weakref
import subprocess
from collections import OrderedDict
from Qt import QtCore, QtGui, QtWidgets
from kombi.ProcessExecution import ProcessExecution
from kombi.TaskHolder.Loader import Loader
from kombi.Template import Template
from kombi.TaskHolder.Dispatcher import Dispatcher
from kombi.Crawler import Crawler, CrawlerContext, PathHolder
from ..Widget.ExecutionSettingsWidget import ExecutionSettingsWidget, ExecutionSettingsWidgetRequiredError
from ..Widget.DispatcherListWidget import DispatcherListWidget
from ..Widget.FilterCrawlerVarWidget import FilterCrawlerVarWidget
from ..Widget.RenderfarmDispatcherPriorityWidget import RenderfarmDispatcherPriorityWidget
from ..Widget.ComboBoxInputDialog import ComboBoxInputDialog
from ..Resource import Resource

try:
    import OpenImageIO # noqa: W0611
except ImportError:
    ImageCrawlerViewer = None
else:
    from ..Widget.ImageCrawlerViewer import ImageCrawlerViewer

class RunnerWindow(QtWidgets.QMainWindow):
    """
    Basic graphical interface to pick files to run through a kombi configuration.

    Deprecation Notice: This interface is going to be phase out in future releases.
    """

    __viewModes = ["group", "flat"]
    __pickerLocation = os.environ.get('KOMBI_GUI_PICKER_LOCATION', '')
    __overridePreviousSelectedLocation = None

    def __init__(self, taskHolders, sourcePaths=[], customHeader='', customCrawlers=[], **kwargs):
        """
        Create a Kombi app.
        """
        super(RunnerWindow, self).__init__(**kwargs)

        self.setStyleSheet(Resource.stylesheet())

        self.__taskHolders = taskHolders

        self.__iconCache = {}
        self.__configurationDirectory = ""
        self.__imageCrawlerViewerAlreadyDisplayed = False
        self.__uiHintSourceColumns = []
        self.__customHeader = customHeader
        self.__verticalSourceScrollBarLatestPos = 0
        self.__customCrawlers = customCrawlers
        self.__crawlerList = None
        self.__messageBox = None
        self.__showVars = False
        self.__showTags = False
        self.__ignoreCheckedEvents = False
        self.__currentSourcePath = None
        self.__buildWidgets()

        # task holders
        assert isinstance(taskHolders, (list, tuple)), "Invalid task holder list!"

        self.__updateSourceColumns(self.__taskHolders)
        self.__onRefreshSourceDir()

        if self.__taskHolders and 'configDirectory' in self.__taskHolders[0].varNames():
            self.__configurationDirectory = self.__taskHolders[0].var('configDirectory')
            self.setWindowTitle('Kombi ({0})'.format(self.__configurationDirectory))

        # getting source files directory from the args
        if sourcePaths:
            self.__sourcePath.setText(';'.join(sourcePaths))

    @classmethod
    def pickConfigurationDirectory(cls, configurationDirectory='', startLocation=""):
        """
        Update the configuration used by kombi.
        """
        # choosing a directory picker dialog
        while not configurationDirectory:
            if configurationDirectory == "":
                configurationDirectory = QtWidgets.QFileDialog.getExistingDirectory(
                    None,
                    "Select a directory with the configuration that should be used by kombi",
                    startLocation,
                    QtWidgets.QFileDialog.ShowDirsOnly
                )

                # cancelled
                if configurationDirectory == "":
                    break

        return configurationDirectory

    @classmethod
    def loadConfigurationTaskHolders(cls, configurationDirectory):
        """
        Display a picker dialog to select a directory containing a kombi configuration.
        """
        # collecting task holders from the directory
        taskHolderLoader = Loader()
        try:
            taskHolderLoader.loadFromDirectory(configurationDirectory)
        except Exception as err:
            traceback.print_exc()

            QtWidgets.QMessageBox.critical(
                None,
                "Kombi",
                "Failed to load the configuration ({0}):\n{1}".format(
                    configurationDirectory,
                    str(err)
                ),
                QtWidgets.QMessageBox.Ok
            )

            raise err

        return taskHolderLoader.taskHolders()

    def updateSource(self, paths):
        """
        Update the source tree.
        """
        self.__sourceTree.clear()
        self.__sourceFilterMenu.clear()
        self.__sourceOverrides = self.__loadSourceOverrides()

        if not paths and not self.__customCrawlers:
            return

        # we want to list in the interface only the crawler types used by the main tasks
        filterTypes = []
        sourceDirectoryCrawlerType = None
        validSourcePath = True
        categoryVarName = None
        collectionVarName = None
        skipSourceStep = False
        validationErrorMessage = "The source path is not compatible with the requirement to run the kombi configuration"
        for taskHolder in self.__taskHolders:
            # checking for source path validation
            if '__uiHintSourceRegExValidation' in taskHolder.varNames():
                validSourcePath = re.match(taskHolder.var('__uiHintSourceRegExValidation'), paths)

                if '__uiHintSourceValidationError' in taskHolder.varNames():
                    validationErrorMessage = taskHolder.var('__uiHintSourceValidationError')

            if '__uiHintShowPreview' in taskHolder.varNames() and taskHolder.var('__uiHintShowPreview') and self.__imageCrawlerViewer and not self.__imageCrawlerViewerAlreadyDisplayed:
                self.__onToggleImageViewer(True)

            if '__uiHintSourceDirectoryCrawlerType' in taskHolder.varNames():
                sourceDirectoryCrawlerType = taskHolder.var('__uiHintSourceDirectoryCrawlerType')

            if '__uiHintCategoryVarName' in taskHolder.varNames():
                categoryVarName = taskHolder.var('__uiHintCategoryVarName')

            if '__uiHintCollectionVarName' in taskHolder.varNames():
                collectionVarName = taskHolder.var('__uiHintCollectionVarName')

            if '__uiHintSkipSourceStep' in taskHolder.varNames():
                skipSourceStep = taskHolder.var('__uiHintSkipSourceStep')

            if '__uiHintTitle' in taskHolder.varNames():
                self.__logo.setTextFormat(QtCore.Qt.RichText)
                self.__logo.setText("<b><big><big> {}".format(taskHolder.var('__uiHintTitle')))

            if '__uiHintIconSize' in taskHolder.varNames():
                iconSize = taskHolder.var('__uiHintIconSize')
                self.__sourceTree.setIconSize(QtCore.QSize(iconSize, iconSize))

            if '__uiHintDispatcher' in taskHolder.varNames():
                self.__selectedDispatcher.selectDispatcher(taskHolder.var('__uiHintDispatcher'))

            if not validSourcePath:
                break

            matchTypes = taskHolder.matcher().matchTypes()

            # if there is a task holder that does not have any type specified to it, then we display all crawlers by
            # passing an empty list to the filter
            if len(matchTypes) == 0:
                filterTypes = []
                break

            filterTypes += taskHolder.matcher().matchTypes()

        # checking for valid source path
        if not validSourcePath:
            QtWidgets.QMessageBox.critical(
                None,
                "Kombi",
                "{}:\n{}".format(
                    validationErrorMessage,
                    paths
                ),
                QtWidgets.QMessageBox.Ok
            )
            return

        # globbing crawlers
        with CrawlerContext():
            if self.__crawlerList is None or self.__currentSourcePath != paths:
                self.__currentSourcePath = paths
                self.__crawlerList = []
                for path in paths.split(";"):
                    if not path:
                        continue

                    if os.path.exists(path):
                        path = PathHolder(path)

                    globCrawlers = []
                    crawler = Crawler.registeredType(sourceDirectoryCrawlerType)(path) if sourceDirectoryCrawlerType else Crawler.create(path)
                    if sourceDirectoryCrawlerType:
                        crawler.setVar('type', sourceDirectoryCrawlerType)

                    if crawler.var('type') in filterTypes:
                        globCrawlers.append(crawler)
                    globCrawlers += crawler.glob(filterTypes)

                    # filtering the result of the glob, but now using the crawler matcher
                    # this will match the variable types.
                    for taskHolder in self.__taskHolders:
                        for crawlerFound in globCrawlers:
                            if crawlerFound in self.__crawlerList:
                                continue

                            if taskHolder.matcher().match(crawlerFound):
                                self.__crawlerList.append(crawlerFound)

                if self.__customCrawlers:
                    # filtering the result of the glob, but now using the crawler matcher
                    # this will match the variable types.
                    for taskHolder in self.__taskHolders:
                        for crawlerFound in self.__customCrawlers:
                            if crawlerFound in self.__crawlerList:
                                continue

                            if taskHolder.matcher().match(crawlerFound):
                                self.__crawlerList.append(crawlerFound)

                # sorting result by name
                self.__crawlerList.sort(key=lambda x: x.var('name').lower() if 'group' not in x.tagNames() else x.tag('group').lower())

                # updating categories (if available)
                if categoryVarName:
                    self.__categoriesDock.widget().refresh(categoryVarName, self.__crawlerList)
                self.__categoriesDock.setVisible(bool(categoryVarName))
            else:
                # in case the user has decided to hit the back button, lets avoid
                # sending back the user to the target options (since the user may
                # want to look the source crawlers)
                skipSourceStep = False

        with CrawlerContext():
            checked = True
            for taskHolder in filter(lambda x: '__uiHintCheckedByDefault' in x.varNames(), self.__taskHolders):
                checked = taskHolder.var('__uiHintCheckedByDefault')

            self.__updateSourceTreeCrawlerList(self.__crawlerList, collectionVarName, checked)
            self.__onSourceFiltersChanged()
            QtWidgets.QApplication.restoreOverrideCursor()

            # forcing kombi to start at the target (next) interface
            if skipSourceStep:
                self.updateTarget()

    def updateTarget(self):
        """
        Update the target tree.
        """
        checkedCrawlers = self.__checkedCrawlers()
        dispatcherName = self.__selectedDispatcher.selectedDispatcher()
        self.__selectedRenderfarmPriority.setVisible(dispatcherName.lower() == "renderfarm")

        # applying overrides
        self.__applySourceOverrides(
            self.__loadSourceOverrides(),
            checkedCrawlers
        )

        self.__targetAreaWidget.setVisible(True)
        self.__selectedDispatcher.setVisible(True)
        self.__sourceAreaWidget.setVisible(False)
        self.__runButton.setEnabled(True)

        self.__nextButton.setVisible(False)
        self.__backButton.setVisible(True)
        self.__runButton.setVisible(True)

        self.__targetTree.updateTarget(checkedCrawlers, self.__taskHolders, self.__checkedViewMode == 'Group')

    def dispatcherWidget(self):
        """
        Return the dispatcher widget.
        """
        return self.__selectedDispatcher

    def setViewMode(self, viewMode):
        """
        Change the view mode.
        """
        assert viewMode in self.__viewModes, "Invalid view mode"

        for action in self.__viewModeActionGroup.actions():
            if action.text().lower() == viewMode.lower():
                action.setChecked(True)

    def viewMode(self):
        """
        Return the current view mode.
        """
        for action in self.__viewModeActionGroup.actions():
            if action.isChecked():
                return action.text().lower()

    def __buildWidgets(self):
        """
        Create the widgets.
        """
        self.setWindowTitle('Kombi')
        self.resize(1280, 720)

        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)

        centralWidget.setLayout(QtWidgets.QVBoxLayout())
        treeArea = QtWidgets.QSplitter()

        sourceLayout = QtWidgets.QVBoxLayout()
        sourceControlMain = QtWidgets.QMainWindow()
        sourceBarLayout = QtWidgets.QHBoxLayout()

        self.__sourcePath = QtWidgets.QLineEdit()
        self.__sourcePath.setReadOnly(True)
        self.__sourceDirButton = QtWidgets.QPushButton()
        self.__sourceDirButton.setToolTip('Selects a source directory')
        self.__sourceDirButton.setIcon(
            Resource.icon("icons/folder.png")
        )

        # refresh
        self.__sourceRefreshButton = QtWidgets.QPushButton()
        self.__sourceRefreshButton.setToolTip('Refreshes the source directory')
        self.__sourceRefreshButton.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload)
        )

        # view mode
        self.__sourceViewModeButton = QtWidgets.QPushButton("View Mode")
        self.__sourceViewModeButton.setToolTip('Changes the view mode')
        self.__sourceViewModeButton.setIcon(
            Resource.icon("icons/viewMode.png")
        )
        self.__sourceViewModeMenu = QtWidgets.QMenu(self.__sourceViewModeButton)
        self.__sourceViewModeButton.setMenu(self.__sourceViewModeMenu)

        # filter
        self.__sourceFilterButton = QtWidgets.QPushButton("Visibility")
        self.__sourceFilterButton.setToolTip('Filters out specific crawler types')
        self.__sourceFilterButton.setIcon(
            Resource.icon("icons/filterView.png")
        )
        self.__sourceFilterMenu = QtWidgets.QMenu(self.__sourceFilterButton)
        self.__sourceFilterButton.setMenu(self.__sourceFilterMenu)

        # filter search
        self.__sourceFilterSearch = QtWidgets.QLineEdit("")
        self.__sourceFilterSearch.setPlaceholderText("Filter...")
        self.__sourceFilterSearch.setClearButtonEnabled(True)
        self.__sourceFilterSearch.setFixedWidth(150)

        self.__sourceDirButton.clicked.connect(self.__onSelectSourceDir)
        self.__sourceRefreshButton.clicked.connect(functools.partial(self.__onRefreshSourceDir, True))
        self.__sourcePath.textChanged.connect(self.updateSource)
        self.__sourceFilterSearchTimer = QtCore.QTimer()
        self.__sourceFilterSearchTimer.setSingleShot(True)
        self.__sourceFilterSearchTimer.timeout.connect(self.__onSourceFiltersChanged)
        self.__sourceFilterSearch.textChanged.connect(self.__onSourceFilterSearch)

        sourceBarLayout.addWidget(self.__sourceDirButton)
        sourceBarLayout.addWidget(self.__sourceRefreshButton)
        sourceBarLayout.addWidget(self.__sourcePath)
        sourceBarLayout.addWidget(self.__sourceFilterSearch)
        sourceBarLayout.addWidget(self.__sourceFilterButton)
        sourceBarLayout.addWidget(self.__sourceViewModeButton)

        sourceLayout.addLayout(sourceBarLayout)

        self.__sourceAreaWidget = QtWidgets.QWidget()
        self.__sourceAreaWidget.setLayout(sourceLayout)

        targetLayout = QtWidgets.QVBoxLayout()

        self.__nextButton = QtWidgets.QPushButton("Next")
        self.__nextButton.setIcon(
            Resource.icon("icons/next.png")
        )
        self.__nextButton.clicked.connect(self.updateTarget)

        self.__backButton = QtWidgets.QPushButton("Back")
        self.__backButton.setIcon(
            Resource.icon("icons/back.png")
        )
        self.__backButton.setVisible(False)
        self.__backButton.clicked.connect(self.__onBack)

        self.__targetAreaWidget = QtWidgets.QWidget()
        self.__targetAreaWidget.setVisible(False)
        self.__targetAreaWidget.setLayout(targetLayout)

        self.__selectedDispatcher = DispatcherListWidget()
        self.__selectedRenderfarmPriority = RenderfarmDispatcherPriorityWidget()
        self.__selectedRenderfarmPriority.setVisible(False)

        targetBarLayout = QtWidgets.QHBoxLayout()
        targetLayout.addLayout(targetBarLayout)

        treeArea.addWidget(self.__sourceAreaWidget)
        treeArea.addWidget(self.__targetAreaWidget)

        self.__sourceTree = self.__treeWidget(["Source"])
        self.__sourceTree.itemChanged.connect(self.__onSourceTreeItemCheckedChanged)
        self.__sourceTree.itemSelectionChanged.connect(self.__onSourceTreeSelectionChanged)
        self.__sourceTree.customContextMenuRequested.connect(self.__onSourceTreeContextMenu)

        self.__targetTree = ExecutionSettingsWidget()

        sourceControlMain.setCentralWidget(self.__sourceTree)

        # categories dock
        self.__categoriesDock = QtWidgets.QDockWidget("Show Categories")
        self.__categoriesDock.setMinimumWidth(150)
        self.__categoriesDock.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)

        self.__categoriesDock.setWidget(FilterCrawlerVarWidget())
        self.__categoriesDock.setVisible(False)
        self.__categoriesDock.widget().filterChangedSignal.connect(self.__onSourceFiltersChanged)

        sourceControlMain.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.__categoriesDock)

        # image viewer
        self.__imageCrawlerViewer = None
        if ImageCrawlerViewer:
            self.__imageCrawlerViewer = QtWidgets.QDockWidget("Preview")
            self.__imageCrawlerViewer.setMinimumWidth(300)
            self.__imageCrawlerViewer.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)

            self.__imageCrawlerViewer.setWidget(ImageCrawlerViewer([], 640, 480))
            self.__imageCrawlerViewer.setVisible(False)

            imageViewerButton = QtWidgets.QPushButton("Preview Panel")
            imageViewerButton.setToolTip('Toggles the display of the preview panel')
            imageViewerButton.setIcon(
                Resource.icon("icons/imageViewer.png")
            )

            sourceControlMain.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.__imageCrawlerViewer)
            sourceBarLayout.addWidget(imageViewerButton)

            imageViewerButton.clicked.connect(self.__onToggleImageViewer)

        sourceLayout.addWidget(sourceControlMain)
        targetLayout.addWidget(self.__targetTree)

        # header
        headerLayout = QtWidgets.QHBoxLayout()
        centralWidget.layout().addLayout(headerLayout)

        self.__logo = QtWidgets.QLabel()
        if self.__customHeader:
            self.__logo.setTextFormat(QtCore.Qt.RichText)
            self.__logo.setText(self.__customHeader)
        else:
            logoFilePath = "icons/header.png"
            if self.__taskHolders[0].var('__uiHintLogo'):
                logoFilePath = self.__taskHolders[0].var('__uiHintLogo')
                if not os.path.isabs(logoFilePath):
                    logoFilePath = os.path.realpath(os.path.join(self.__taskHolders[0].var('configDirectory'), logoFilePath))

            self.__logo.setPixmap(Resource.pixmap(logoFilePath).scaledToHeight(64, QtCore.Qt.SmoothTransformation))
        self.__logo.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        headerLayout.addWidget(self.__logo)
        headerLayout.addStretch()

        centralWidget.layout().addWidget(treeArea)
        buttonLayout = QtWidgets.QHBoxLayout()
        centralWidget.layout().addLayout(buttonLayout)

        self.__runButton = QtWidgets.QPushButton('Run')
        self.__runButton.setVisible(False)
        self.__runButton.setToolTip('Performs the tasks')
        self.__runButton.setIcon(
            Resource.icon("icons/run.png")
        )
        self.__runButton.clicked.connect(self.__onPerformTasks)

        buttonLayout.addWidget(self.__selectedDispatcher)
        buttonLayout.addWidget(self.__selectedRenderfarmPriority)

        buttonLayout.addStretch()
        buttonLayout.addWidget(self.__backButton)
        buttonLayout.addWidget(self.__nextButton)
        buttonLayout.addWidget(self.__runButton)

        # updating view mode
        self.__viewModeActionGroup = QtWidgets.QActionGroup(self)
        self.__checkedViewMode = None
        for viewMode in self.__viewModes:
            viewAction = self.__sourceViewModeMenu.addAction(viewMode.capitalize())
            viewAction.setActionGroup(self.__viewModeActionGroup)
            viewAction.setCheckable(True)
            viewAction.changed.connect(self.__onChangeView)

            if (viewMode == self.__viewModes[0]):
                viewAction.setChecked(True)

    def __onSourceTreeSelectionChanged(self):
        if not (self.__imageCrawlerViewer and self.__imageCrawlerViewer.isVisible()):
            return

        crawlers = []
        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            if hasattr(selectedItem, 'crawlers'):
                for crawler in selectedItem.crawlers:
                    if crawler.isLeaf():
                        crawlers.append(crawler)
                    else:
                        with CrawlerContext():
                            for chilCrawler in crawler.children():
                                crawlers.append(chilCrawler)

        self.__imageCrawlerViewer.widget().setCrawlers(crawlers)

    def __onToggleImageViewer(self, forceVisibility=False):
        """
        Slot triggered when the image preview button is pressed.
        """
        self.__imageCrawlerViewer.setVisible(not self.__imageCrawlerViewer.isVisible() or forceVisibility)

        if self.__imageCrawlerViewer.isVisible() or forceVisibility:
            if not self.__imageCrawlerViewerAlreadyDisplayed:
                self.__imageCrawlerViewerAlreadyDisplayed = True
                self.__imageCrawlerViewer.parent().resizeDocks([self.__imageCrawlerViewer], [400], QtCore.Qt.Horizontal)
                self.resize(self.width() + 300, self.height())

            self.__onSourceTreeSelectionChanged()

    def __updateSourceColumns(self, taskHolders):
        """
        Update the source columns.
        """
        # updating columns
        columns = []
        for taskHolder in filter(lambda x: '__uiHintSourceColumns' in x.varNames(), taskHolders):
            for columnName in filter(lambda x: x not in columns, taskHolder.var('__uiHintSourceColumns')):
                columns.append(columnName)

        # fix-me: workaround necessary to avoid the bug of not showing
        # the options properly inside of the target tree
        if not len(columns):
            columns.append(' ')

        if columns != self.__uiHintSourceColumns:
            self.__uiHintSourceColumns = columns
            header = QtWidgets.QTreeWidgetItem(
                ["Source"] + list(map(self.__camelCaseToSpaced, self.__uiHintSourceColumns))
            )

            self.__sourceTree.setHeaderItem(
                header
            )

            self.__targetTree.setHeaderItem(
                QtWidgets.QTreeWidgetItem(
                    ("", "")
                )
            )

    def __updateSourceTreeCrawlerList(self, crawlerList, collectionVarName, checked=True):
        """
        Update the crawlers displayed in the source tree.
        """
        crawlerTypes = set()
        crawlerTags = {}
        collectionParents = OrderedDict()

        # processing collections
        if collectionVarName:
            collections = set()
            for crawler in crawlerList:
                if collectionVarName in crawler.varNames():
                    collectionName = crawler.var(collectionVarName)
                    collections.add(collectionName)

            for collectionName in sorted(collections, key=lambda x: str(x).lower()):
                collectionParent = QtWidgets.QTreeWidgetItem(self.__sourceTree)
                collectionParent.setExpanded(True)
                collectionParent.setFlags(collectionParent.flags() & ~QtCore.Qt.ItemIsUserCheckable)
                collectionParent.setData(0, QtCore.Qt.EditRole, collectionName)
                collectionParents[collectionName] = collectionParent

        # workaround necessary to improve the rendering speed
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.__sourceTree.setVisible(False)

        # group
        if self.__checkedViewMode == "Group":
            groupedCrawlers = self.__groupCrawlers(crawlerList)

            for groupName in groupedCrawlers.keys():
                if groupName:
                    parent = QtWidgets.QTreeWidgetItem(collectionParents[groupedCrawlers[0].var(collectionVarName)] if collectionParents and collectionVarName in groupedCrawlers[0].varNames() else self.__sourceTree)
                    self.__updateIcon(parent, groupedCrawlers[groupName][0])
                    parent.crawlers = list(groupedCrawlers[groupName])
                    parent.setExpanded(len(groupedCrawlers) == 2 and not groupedCrawlers[None])

                    # visible data
                    visibleGroupName = groupName + '   '
                    if visibleGroupName.startswith(os.sep):
                        visibleGroupName = visibleGroupName[1:]

                    parent.setData(0, QtCore.Qt.EditRole, visibleGroupName)

                    # adding column information
                    self.__addSourceTreeColumnData(groupedCrawlers[groupName][0], parent, groupedCrawlers[groupName])

                    parent.setFlags(parent.flags() | QtCore.Qt.ItemIsUserCheckable)

                    # check state
                    parent.setCheckState(0, QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)

                    for crawler in groupedCrawlers[groupName]:
                        self.__createSourceTreeChildItem(
                            crawler,
                            parent,
                            crawlerTypes,
                            crawlerTags
                        )

                else:
                    for crawler in groupedCrawlers[groupName]:
                        child = self.__createSourceTreeChildItem(
                            crawler,
                            collectionParents[crawler.var(collectionVarName)] if collectionParents and collectionVarName in crawler.varNames() else self.__sourceTree,
                            crawlerTypes,
                            crawlerTags
                        )

                        if groupName is None and len(groupedCrawlers) == 1 and len(groupedCrawlers[None]) == 1:
                            child.setExpanded(True)

                        child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)

                        # check state
                        child.setCheckState(0, QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)

                        self.__addSourceTreeColumnData(crawler, child)

        # flat
        else:
            for crawler in sorted(crawlerList, key=lambda x: x.var('fullPath')):

                # only testing with the first crawler when grouped
                if isinstance(crawler, list):
                    crawler = crawler[0]

                child = self.__createSourceTreeChildItem(crawler, self.__sourceTree, crawlerTypes, crawlerTags)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)

                # check state
                child.setCheckState(0, QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)

                self.__addSourceTreeColumnData(crawler, child)

        # crawler info
        self.__crawlerInfoMenu = self.__sourceFilterMenu.addMenu('Crawler Info')

        # vars
        self.__showVarsAction = self.__crawlerInfoMenu.addAction('Vars')
        self.__showVarsAction.setCheckable(True)
        self.__showVarsAction.setChecked(self.__showVars)
        self.__showVarsAction.triggered.connect(self.__onFilterShowVars)

        # tags
        self.__showTagsAction = self.__crawlerInfoMenu.addAction('Tags')
        self.__showTagsAction.setCheckable(True)
        self.__showTagsAction.setChecked(self.__showTags)
        self.__showTagsAction.triggered.connect(self.__onFilterShowTags)

        # crawler types
        self.__crawlerTypesMenu = self.__sourceFilterMenu.addMenu('Crawler Types')

        allAction = self.__crawlerTypesMenu.addAction('ALL')
        allAction.triggered.connect(self.__onFilterSelectAll)

        noneAction = self.__crawlerTypesMenu.addAction('NONE')
        noneAction.triggered.connect(self.__onFilterSelectNone)
        self.__crawlerTypesMenu.addSeparator()

        # workaround to improve the performance of the rendering:
        # restoring the visibility of the widget
        self.__sourceTree.setVisible(True)

        for crawlerType in sorted(crawlerTypes):
            action = self.__crawlerTypesMenu.addAction(crawlerType)
            action.setCheckable(True)
            action.setChecked(True)
            action.changed.connect(self.__onSourceFiltersChanged)

        self.__sourceTree.resizeColumnToContents(0)

    def __groupCrawlers(self, crawlers):
        """
        Return a dictionary containing the matched crawlers grouped.
        """
        groupedCrawlers = OrderedDict()
        groupedCrawlers[None] = []
        for crawlerList in Crawler.group(crawlers):
            for crawler in crawlerList:
                # group
                if self.__checkedViewMode == 'Group' and 'group' in crawler.tagNames():
                    groupName = crawler.tag('group')
                    if groupName not in groupedCrawlers:
                        groupedCrawlers[groupName] = []

                    groupedCrawlers[groupName].append(crawler)

                # flat
                else:
                    groupedCrawlers[None].append(crawler)

        return groupedCrawlers

    def __showInFileManager(self, filePaths):
        """
        Open the input file path in the default app.
        """
        args = []
        commonPaths = {}
        for filePath in filePaths:
            parentDir = os.path.dirname(filePath)
            if parentDir not in commonPaths:
                commonPaths[parentDir] = set()
            commonPaths[parentDir].add(filePath)

        finalPaths = []
        for commonPath, paths in commonPaths.items():
            if len(paths) > 1:
                finalPaths.append(commonPath)
            else:
                finalPaths.append(list(paths)[0])

        # linux
        if platform.system() == 'Linux':
            # args = ('xdg-open', filePath)
            args.append('nautilus')
            args += finalPaths
        # windows
        elif platform.system() == 'Windows':
            args = ('explorer.exe', '/select,' + filePaths[0].replace('/', '\\'))
        # macos
        elif platform.system() == 'Darwin':
            args = ('open', filePaths)

        assert args

        env = dict(os.environ)
        if 'PYTHONHOME' in env:
            del env['PYTHONHOME']

        if 'LD_LIBRARY_PATH' in env:
            del env['LD_LIBRARY_PATH']

        subprocess.Popen(args, env=env)

    def __treeWidget(self, columns=[]):
        """
        Return a tree widget used by source and target.
        """
        sourceTree = QtWidgets.QTreeWidget()
        sourceTree.sortByColumn(0, QtCore.Qt.AscendingOrder)
        sourceTree.setSortingEnabled(True)
        sourceTree.setAlternatingRowColors(True)

        sourceTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        sourceTree.setSelectionBehavior(QtWidgets.QTreeWidget.SelectItems)
        sourceTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        header = QtWidgets.QTreeWidgetItem(columns)
        sourceTree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        sourceTree.setHeaderItem(header)

        return sourceTree

    def __checkedCrawlers(self):
        """
        Return a list of checked crawlers in the source tree.
        """
        totalRows = self.__sourceTree.model().rowCount()
        result = []
        for i in range(totalRows):
            self.__sourceTree.model().index(i, 0)
            item = self.__sourceTree.topLevelItem(i)

            # collections
            if not hasattr(item, 'crawlers'):
                for childIndex in range(item.childCount()):
                    childItem = item.child(childIndex)
                    if childItem.checkState(0) and hasattr(childItem, 'crawlers'):
                        result.extend(childItem.crawlers)

            # root items
            elif item.checkState(0) and hasattr(item, 'crawlers'):
                result.extend(item.crawlers)

        return list(map(lambda x: x.clone(), result))

    def __sourceOverridesConfig(self):
        """
        Return the full path about the location for the override files.
        """
        sourcePath = self.__sourcePath.text()

        return os.path.join(
            self.__configurationDirectory,
            "overrides",
            "{}_{}.json".format(
                getpass.getuser(),
                hashlib.md5(sourcePath.encode('utf-8')).hexdigest()
            )
        )

    def __loadSourceOverrides(self):
        """
        Load crawler overrides in the source tree.
        """
        result = {}

        if os.path.exists(self.__sourceOverridesConfig()):
            with open(self.__sourceOverridesConfig()) as sourceFile:
                result = json.load(sourceFile)
                if result and "overrides" in result:
                    result = result["overrides"]

        return result

    def __applySourceOverrides(self, overrides, crawlers):
        """
        Apply overrides overrides on the source tree.
        """
        if not overrides:
            return

        with CrawlerContext():
            def __allCrawlers(childCrawler):
                fullPath = childCrawler.var('fullPath')
                if fullPath in overrides:
                    for varName, varValue in overrides[fullPath].items():
                        childCrawler.setVar(
                            varName,
                            varValue,
                            varName in childCrawler.contextVarNames()
                        )

                if not childCrawler.isLeaf():
                    for crawler in childCrawler.children():
                        __allCrawlers(crawler)

            for crawler in crawlers:
                __allCrawlers(crawler)

    def __addSourceTreeColumnData(self, crawler, treeItem, groupedCrawlers=None):
        """
        Add crawler information to a column in the source tree.
        """
        # adding column information
        for index, column in enumerate(self.__uiHintSourceColumns):

            hasOverride = False
            value = ''
            columnLabel = ''
            mixedValues = False
            for crawlerIndex, checkCrawler in enumerate(groupedCrawlers if groupedCrawlers else [crawler]):
                currentValue = ''
                if checkCrawler.var('fullPath') in self.__sourceOverrides and column in self.__sourceOverrides[checkCrawler.var('fullPath')]:
                    currentValue = self.__sourceOverrides[checkCrawler.var('fullPath')][column]
                    hasOverride = True
                if column in checkCrawler.varNames():
                    if not hasOverride:
                        currentValue = checkCrawler.var(column)

                if currentValue != value and crawlerIndex:
                    mixedValues = True
                    break
                value = currentValue

            columnLabel = ('mixed' if mixedValues else str(value)) + '   '

            # creating custom widget to show the presets
            if '{}.button'.format(column) in crawler.tagNames():
                columnButton = QtWidgets.QPushButton(self)
                columnButton.setObjectName('columnButton')
                columnButton.setText(str(value))
                columnButton.clicked.connect(functools.partial(self.__onColumnButton, weakref.ref(treeItem), crawler.tag('{}.button'.format(column))))
                self.__sourceTree.setItemWidget(treeItem, index + 1, columnButton)

            # creating custom widget to show the presets
            elif '{}.presets'.format(column) in crawler.tagNames() or value is not None and isinstance(value, bool):
                columnLabel += "          "
                presetsHolderWidget = QtWidgets.QWidget(self)
                presetsHolderWidget.setObjectName('presetTreeHolder')
                presetsArrowIcon = QtWidgets.QPushButton(self)
                presetsArrowIcon.setObjectName('presetTreeButton')
                presetsArrowIcon.setFixedWidth(28)
                presetsArrowIcon.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarUnshadeButton))
                presetsArrowIcon.setFlat(True)
                presetsArrowIcon.clicked.connect(functools.partial(self.__onSourceTreePresetsClicked, weakref.ref(treeItem), index + 1))

                presetsLayout = QtWidgets.QHBoxLayout(presetsHolderWidget)
                presetsLayout.setContentsMargins(0, 0, 0, 0)
                presetsLayout.addStretch()
                presetsLayout.addWidget(presetsArrowIcon)

                self.__sourceTree.setItemWidget(treeItem, index + 1, presetsHolderWidget)

            treeItem.setData(
                index + 1,
                QtCore.Qt.EditRole,
                columnLabel
            )

            if mixedValues:
                treeItem.setForeground(
                    index + 1,
                    QtGui.QBrush(QtGui.QColor(100, 100, 100))
                )

            elif value == '' and column in crawler.varNames() and \
                    (not crawler.tag('{}.allowEmpty'.format(column)) if '{}.allowEmpty'.format(column) in crawler.tagNames() else True):
                font = QtGui.QFont()
                font.setBold(True)

                treeItem.setData(
                    index + 1,
                    QtCore.Qt.EditRole,
                    'empty'
                )

                treeItem.setFont(
                    index + 1,
                    font
                )

                treeItem.setForeground(
                    index + 1,
                    QtGui.QBrush(QtGui.QColor(100, 70, 70))
                )

            elif hasOverride:
                font = QtGui.QFont()
                font.setItalic(True)
                treeItem.setFont(
                    index + 1,
                    font
                )

                treeItem.setForeground(
                    index + 1,
                    QtGui.QBrush(QtGui.QColor(255, 152, 28))
                )

    def __createSourceTreeChildItem(self, crawler, parent, crawlerTypes, crawlerTags):
        """
        Create a new child item in the source tree.
        """
        child = QtWidgets.QTreeWidgetItem(parent)
        child.crawlers = [crawler]
        self.__updateIcon(child, crawler)

        # visible data
        child.setData(0, QtCore.Qt.EditRole, crawler.var('baseName') + '   ')
        self.__addSourceTreeColumnData(crawler, child)

        crawlerTypes.add(crawler.var('type'))

        ####
        if not crawler.isLeaf():
            childEntries = QtWidgets.QTreeWidgetItem(child)
            childEntries.setData(
                0,
                QtCore.Qt.EditRole,
                'children'
            )
            childEntries.setExpanded(True)
            groupedCrawlers = self.__groupCrawlers(crawler.children())
            for groupName in groupedCrawlers.keys():
                if groupName:
                    parent = QtWidgets.QTreeWidgetItem(childEntries)
                    parent.crawlers = list(groupedCrawlers[groupName])
                    self.__updateIcon(parent, groupedCrawlers[groupName][0])

                    # visible data
                    visibleGroupName = groupName + '   '
                    if visibleGroupName.startswith(os.sep):
                        visibleGroupName = visibleGroupName[1:]

                    parent.setData(0, QtCore.Qt.EditRole, visibleGroupName)

                    # adding column information
                    self.__addSourceTreeColumnData(groupedCrawlers[groupName][0], parent, groupedCrawlers[groupName])
                    for childCrawler in groupedCrawlers[groupName]:
                        self.__createSourceTreeChildItem(
                            childCrawler,
                            parent,
                            crawlerTypes,
                            crawlerTags
                        )
                else:
                    for childCrawler in groupedCrawlers[groupName]:
                        self.__createSourceTreeChildItem(
                            childCrawler,
                            childEntries,
                            crawlerTypes,
                            crawlerTags
                        )

        if self.__showVars:
            variables = QtWidgets.QTreeWidgetItem(child)
            variables.setData(
                0,
                QtCore.Qt.EditRole,
                'vars'
            )
            for varName in sorted(crawler.varNames()):
                if varName in ['path']:
                    continue

                variablesChild = QtWidgets.QTreeWidgetItem(variables)
                variablesChild.setData(
                    0,
                    QtCore.Qt.EditRole,
                    '{0}={1}'.format(varName, crawler.var(varName))
                )

        if self.__showTags:
            tags = QtWidgets.QTreeWidgetItem(child)
            tags.setData(
                0,
                QtCore.Qt.EditRole,
                'tags'
            )

            for tagName in crawler.tagNames():
                tagValue = crawler.tag(tagName)
                if not isinstance(tagValue, str):
                    continue

                if tagName not in crawlerTags:
                    crawlerTags[tagName] = set()
                crawlerTags[tagName].add(tagValue)

            for tagName in sorted(crawler.tagNames()):
                tagChild = QtWidgets.QTreeWidgetItem(tags)
                tagChild.setData(
                    0,
                    QtCore.Qt.EditRole,
                    '{0}={1}'.format(tagName, crawler.tag(tagName))
                )

        return child

    def __onBack(self):
        """
        Slot triggered when back button is triggered.
        """
        self.__selectedDispatcher.setVisible(False)
        self.__selectedRenderfarmPriority.setVisible(False)
        self.__backButton.setVisible(False)
        self.__nextButton.setVisible(True)
        self.__runButton.setVisible(False)
        self.__sourceAreaWidget.setVisible(True)
        self.__targetAreaWidget.setVisible(False)

    def __onChangeView(self):
        """
        Slot triggered when change view mode is triggered.
        """
        checkedAction = self.__viewModeActionGroup.checkedAction()
        if checkedAction and checkedAction.text() != self.__checkedViewMode:
            self.__checkedViewMode = self.__viewModeActionGroup.checkedAction().text()
            self.__onRefreshSourceDir()

    def __onPerformTasks(self):
        """
        Slot triggered when run button is triggered.
        """
        if self.__messageBox:
            self.__messageBox.reject()
        self.__runButton.setEnabled(False)
        if not self.__targetTree.model().rowCount():
            QtWidgets.QMessageBox.information(
                self,
                "Kombi",
                "No targets available (refresh the targets)!",
                QtWidgets.QMessageBox.Ok
            )
            return

        output = ''
        dispatcherName = self.__selectedDispatcher.selectedDispatcher()
        dispatcherPriority = None
        if dispatcherName.lower() == "renderfarm":
            dispatcherPriority = self.__selectedRenderfarmPriority.selectedPriorityValue()

        try:
            for taskHolder, crawlersGroup in self.__targetTree.executionTaskHolders():

                # replacing the priority for the tasks
                if dispatcherPriority:
                    for childTask in taskHolder.childTasks():
                        childTask.setMetadata("dispatch.renderFarm.priority", dispatcherPriority)

                dispatcher = Dispatcher.create(dispatcherName)

                # applying overrides
                self.__applySourceOverrides(
                    self.__loadSourceOverrides(),
                    crawlersGroup
                )

                # default label
                label = "{}/{} [{}]".format(
                    os.path.basename(taskHolder.var('configDirectory')),
                    crawlersGroup[0].tag('group') if 'group' in crawlersGroup[0].tagNames() else crawlersGroup[0].var('baseName'),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                # custom label
                if taskHolder.task().hasMetadata('dispatch.label'):
                    label = Template(
                        "{} [{}]".format(
                            taskHolder.task().metadata('dispatch.label'),
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                    ).valueFromCrawler(crawlersGroup[0])

                dispatcher.setOption('label', label)
                dispatcher.setOption('priority', 20)

                for result in dispatcher.dispatch(taskHolder, crawlersGroup):
                    if isinstance(result, ProcessExecution):
                        output += result.stdoutContent()
                    else:
                        output += 'Dispatched to {}: {}'.format(dispatcherName, result)

        except Exception as err:
            traceback.print_exc()

            self.__messageBox = QtWidgets.QMessageBox(
                self,
                "Kombi",
                QtWidgets.QMessageBox.Ok
            )
            self.__messageBox.setWindowModality(QtCore.Qt.NonModal)
            self.__messageBox.setIcon(QtWidgets.QMessageBox.Critical)
            self.__messageBox.setText('Failed during execution')
            self.__messageBox.setDetailedText(str(err))

            if isinstance(err, ExecutionSettingsWidgetRequiredError):
                self.__messageBox.setWindowTitle('Failed on validating task: {}'.format(err.task().type()))
                self.__messageBox.setIcon(QtWidgets.QMessageBox.NoIcon)
                self.__messageBox.setText(str(err))

                horizontalSpacer = QtWidgets.QSpacerItem(1000, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
                layout = self.__messageBox.layout()
                layout.addItem(horizontalSpacer, layout.rowCount(), 0, 1, layout.columnCount())

                self.__runButton.setEnabled(True)
                self.__messageBox.show()
                return

            self.__messageBox.show()

            raise err

        else:
            if not ('__uiHintCloseAfterExecution' not in taskHolder.varNames() or bool(taskHolder.var('__uiHintCloseAfterExecution')) is False):
                self.close()
                return

            message = "Execution completed!"
            if dispatcherName == 'renderFarm':
                message = "Execution submitted to the farm!"

            QtWidgets.QMessageBox.information(
                self,
                "Kombi",
                message,
                QtWidgets.QMessageBox.Ok
            )

            # showing the output for local executions
            if not dispatcherName == 'renderFarm':
                self.__outputWidget = QtWidgets.QPlainTextEdit()
                self.__outputWidget.setPlainText(output)
                self.__outputWidget.setWindowTitle('Output')
                self.__outputWidget.setMinimumWidth(920)
                self.__outputWidget.setMinimumHeight(600)
                self.__outputWidget.setVisible(True)
                self.__outputWidget.setReadOnly(True)

    def __onColumnButton(self, treeItemWeakRef, callableName):
        """
        Slot triggered when the column button is clicked.
        """
        crawlers = treeItemWeakRef().crawlers

        # executing callable
        for index, crawler in enumerate(crawlers):
            if hasattr(crawler, callableName):
                try:
                    getattr(crawlers[0], callableName)(index, len(crawlers))
                except Exception as err:
                    traceback.print_exc()

                    QtWidgets.QMessageBox.critical(
                        None,
                        "Kombi",
                        "Error during the execution {}:\n\n{}".format(str(crawler), str(err)),
                        QtWidgets.QMessageBox.Ok
                    )

                    raise err
            else:
                QtWidgets.QMessageBox.critical(
                    None,
                    "Kombi",
                    'Could not find callable "{0}" in crawler "{1}"'.format(
                        callableName,
                        str(crawlers[0].var('type'))
                    ),
                    QtWidgets.QMessageBox.Ok
                )

    def __onSourceTreePresetsClicked(self, treeItemWeakRef, columnIndex):
        """
        Slot triggered when the preset arrow button is clicked.
        """
        currentIndex = self.__sourceTree.indexFromItem(treeItemWeakRef(), columnIndex)

        # reseting the selection in case the clicked item is not part of
        # the selection
        if currentIndex not in self.__sourceTree.selectionModel().selectedIndexes():
            self.__sourceTree.selectionModel().select(currentIndex, QtCore.QItemSelectionModel.SelectCurrent)

        self.__onChangeCrawlerValue()

    def __onSourceTreeContextMenu(self, point=None):
        """
        Slot triggered when context menu from source tree is triggered.
        """
        self.__sourceTree.resizeColumnToContents(0)

        selectedIndexes = self.__sourceTree.selectionModel().selectedIndexes()

        if selectedIndexes:
            selectedColumn = selectedIndexes[0].column()
            menu = QtWidgets.QMenu(self)
            if selectedColumn == 0:
                action = menu.addAction('Show in file manager')
                action.triggered.connect(self.__onOpenSelected)

                action = menu.addAction('Play in RV')
                action.triggered.connect(self.__onPlayInRV)

                # action = menu.addAction('Show Folder')
                # action.triggered.connect(self.__onShowFolder)
            else:
                action = menu.addAction('Override Value')
                action.triggered.connect(self.__onChangeCrawlerValue)

                action = menu.addAction('Reset Value')
                action.triggered.connect(self.__onResetCrawlerValue)

            menu.exec_(self.__sourceTree.mapToGlobal(point) if point is not None else QtGui.QCursor.pos())

    def __onChangeCrawlerValue(self):
        """
        Slot triggered when an override in the source tree is triggered.
        """
        value = None
        overrides = dict(self.__sourceOverrides)

        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            crawlers = []
            if hasattr(selectedItem, 'crawlers'):
                crawlers = selectedItem.crawlers[:]
            if not crawlers:
                continue

            selectedColumn = selectedIndex.column()
            columnName = self.__uiHintSourceColumns[selectedColumn - 1]

            hintValue = ""
            fileChooserName = '{}.fileChooserOnOverride'.format(columnName)
            showFileChooser = fileChooserName in crawlers[0].tagNames() and crawlers[0].tag(fileChooserName)
            if columnName in crawlers[0].varNames():
                hintValue = crawlers[0].var(columnName)

            if value is None:
                allPresets = []

                if hintValue is not None and isinstance(hintValue, bool):
                    allPresets.append('True')
                    allPresets.append('False')
                else:
                    presetsName = '{}.presets'.format(columnName)
                    for crawlerItem in crawlers:
                        if presetsName not in crawlerItem.tagNames():
                            continue

                        for presetValue in crawlerItem.tag(presetsName):
                            if presetValue not in allPresets:
                                allPresets.append(presetValue)

                    if len(crawlers) > 1:
                        allPresets.sort(key=lambda x: str(x).lower())

                if allPresets:
                    promptDialog = ComboBoxInputDialog(
                        allPresets,
                        title="Override Value",
                        helpText="New value for: {}".format(columnName)
                    )
                    # cancelled
                    if not promptDialog.exec_():
                        return
                    value = promptDialog.currentText()
                else:
                    if showFileChooser:
                        ext = None
                        if '{}.fileChooserOnOverrideAllowedExt'.format(columnName) in crawlers[0].tagNames():
                            ext = "{ext} (*.{ext})".format(
                                ext=crawlers[0].tag('{}.fileChooserOnOverrideAllowedExt'.format(columnName))
                            )

                        value = QtWidgets.QFileDialog.getOpenFileName(
                            self,
                            "Select a file to override: {}".format(
                                crawlers[0].var('baseName')
                            ),
                            self.__overridePreviousSelectedLocation,
                            ext
                        )

                        if not value:
                            return
                        value = value[0]

                        self.__overridePreviousSelectedLocation = os.path.dirname(value)
                    else:
                        value = QtWidgets.QInputDialog.getText(
                            self,
                            "Override value",
                            "New value for: {}".format(columnName),
                            QtWidgets.QLineEdit.Normal,
                            str(hintValue)
                        )

                        # cancelled
                        if not value[1]:
                            return
                        value = value[0]

                value = type(hintValue)(value) if type(hintValue) is not bool else value.lower() == 'true'

            for crawlerItem in crawlers:
                crawlerFullPath = crawlerItem.var('fullPath')

                # skipping the same value that is currently set in the crawler
                if value == crawlerItem.var(columnName):
                    if crawlerFullPath in overrides and columnName in overrides[crawlerFullPath]:
                        del overrides[crawlerFullPath][columnName]
                    continue

                # adding
                if crawlerFullPath not in overrides:
                    overrides[crawlerFullPath] = {}

                overrides[crawlerFullPath][columnName] = value

        if not os.path.exists(os.path.dirname(self.__sourceOverridesConfig())):
            os.mkdir(os.path.dirname(self.__sourceOverridesConfig()))

        with open(self.__sourceOverridesConfig(), 'w') as sourceFile:
            data = {
                "sourcePath": self.__sourcePath.text(),
                "overrides": overrides
            }

            json.dump(data, sourceFile, indent=4)

        if value is not None:
            self.__onRefreshSourceDir()

    def __onResetCrawlerValue(self):
        """
        Slot triggered when an override in the source tree is removed.
        """
        overrides = dict(self.__sourceOverrides)

        selectedCrawlers = set()
        columnNames = set()
        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            crawlers = []
            if hasattr(selectedItem, 'crawlers'):
                crawlers = selectedItem.crawlers[:]
            if not crawlers:
                continue

            selectedColumn = selectedIndex.column()
            columnName = self.__uiHintSourceColumns[selectedColumn - 1]

            selectedCrawlers.update(crawlers)
            columnNames.add(columnName)

        for fullPath in map(lambda x: x.var('fullPath'), selectedCrawlers):
            if fullPath not in overrides:
                continue

            for columnName in columnNames:
                if columnName in overrides[fullPath]:
                    del overrides[fullPath][columnName]

                if not len(overrides[fullPath]):
                    del overrides[fullPath]

        if os.path.exists(os.path.dirname(self.__sourceOverridesConfig())):
            with open(self.__sourceOverridesConfig(), 'w') as sourceFile:
                data = {
                    "sourcePath": self.__sourcePath.text(),
                    "overrides": overrides
                }
                json.dump(data, sourceFile, indent=4)

            self.__onRefreshSourceDir()

    def __onShowFolder(self):
        """
        Slot triggered when show folder for the selected crawlers is triggered.
        """
        folderPaths = set()
        for crawler in self.__selectedCrawlers():
            if crawler.isLeaf():
                folderPaths.add(os.path.dirname(crawler.var('fullPath')))
            else:
                folderPaths.add(crawler.var('fullPath'))

        for folderPath in folderPaths:
            self.__showInFileManager(
                folderPath
            )

    def __selectedCrawlers(self):
        """
        Return a list of selected crawlers.
        """
        selectedCrawlers = set()
        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            crawlers = []
            if hasattr(selectedItem, 'crawlers'):
                crawlers = selectedItem.crawlers[:]
            if not crawlers:
                continue

            selectedCrawlers.update(crawlers)

        return list(selectedCrawlers)

    def __onOpenSelected(self):
        """
        Slot triggered when open the select file is triggered.
        """
        crawlers = self.__selectedCrawlers()
        if not crawlers:
            return
        self.__showInFileManager(list(map(lambda x: x.var('fullPath'), crawlers)))

    def __onPlayInRV(self):
        """
        Slot triggered when the option play in rv is selected.
        """
        crawlers = self.__selectedCrawlers()
        if not crawlers:
            return

        commonPaths = {}
        for filePath in map(lambda x: x.var('fullPath'), crawlers):
            parentDir = os.path.dirname(filePath)
            if parentDir not in commonPaths:
                commonPaths[parentDir] = set()
            commonPaths[parentDir].add(filePath)

        finalPaths = []
        for commonPath, paths in commonPaths.items():
            if len(paths) > 1:
                finalPaths.append(commonPath)
            else:
                finalPaths.append(list(paths)[0])

        env = dict(os.environ)
        if 'PYTHONHOME' in env:
            del env['PYTHONHOME']

        if 'LD_LIBRARY_PATH' in env:
            del env['LD_LIBRARY_PATH']

        subprocess.Popen(' '.join(['rv'] + finalPaths), shell=True, env=env)

    def __onSelectSourceDir(self):
        """
        Slot triggered when select source button is triggered.
        """
        self.__verticalSourceScrollBarLatestPos = 0
        currentDir = self.__sourcePath.text() or self.__pickerLocation
        selectedDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select source directory",
            currentDir,
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if selectedDirectory not in ['', '/']:
            self.__sourcePath.setText(selectedDirectory)
            self.__sourcePath.setText(selectedDirectory)

    def __onRefreshSourceDir(self, force=False):
        """
        Slot triggered when refresh button from source tree is triggered.
        """
        self.__verticalSourceScrollBarLatestPos = self.__sourceTree.verticalScrollBar().value()
        self.__sourceTree.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        # collecting the current state of the tree
        treeData = {}
        for index in range(self.__sourceTree.topLevelItemCount()):
            item = self.__sourceTree.topLevelItem(index)
            treeData[(index, item.text(0))] = {
                "checked": item.checkState(0),
                "expanded": item.isExpanded()
            }

        # refreshing tree
        if force:
            self.__crawlerList = None

        self.updateSource(self.__sourcePath.text())

        # reapplying the state
        for index in range(self.__sourceTree.topLevelItemCount()):
            item = self.__sourceTree.topLevelItem(index)
            key = (index, item.text(0))

            if key in treeData:
                if bool(item.flags() & QtCore.Qt.ItemIsUserCheckable):
                    item.setCheckState(0, treeData[key]["checked"])
                item.setExpanded(treeData[key]["expanded"])

        # workaround necessary to restore the position of the scrollbar
        QtCore.QTimer.singleShot(0, self.__onRestoreVerticalScrollBar)

    def __onRestoreVerticalScrollBar(self):
        """
        Slot triggered to restore the vertical scrollbar position.
        """
        self.__sourceTree.verticalScrollBar().setSliderPosition(self.__verticalSourceScrollBarLatestPos)

    def __onFilterShowVars(self, *args):
        """
        Slot triggered when info show vars is triggered.
        """
        self.__showVars = self.__showVarsAction.isChecked()

        self.__onRefreshSourceDir()

    def __onFilterShowTags(self, *args):
        """
        Slot triggered when info show tags is triggered.
        """
        self.__showTags = self.__showTagsAction.isChecked()

        self.__onRefreshSourceDir()

    def __onFilterSelectNone(self):
        """
        Slot triggered when select none filter is triggered.
        """
        for action in self.__crawlerTypesMenu.actions():
            action.setChecked(False)

    def __onFilterSelectAll(self):
        """
        Slot triggered when select all filter is triggered.
        """
        for action in self.__crawlerTypesMenu.actions():
            action.setChecked(True)

    def __onSourceFilterSearch(self, *args, **kwargs):
        """
        Slot triggered every time the filter search field is changed.
        """
        self.__sourceFilterSearchTimer.start(500)

    def __onSourceFiltersChanged(self, *args, **kwargs):
        """
        Slot triggered a filter is changed in the source tree.
        """
        visibleTypes = []
        for action in self.__crawlerTypesMenu.actions():
            if action.isChecked():
                visibleTypes.append(action.text())

        # custom filter
        filterVarName = self.__categoriesDock.widget().filterVarName()
        filterVarValues = []
        if filterVarName:
            filterVarValues = self.__categoriesDock.widget().checkedFilterVarValues()

        allTreeItems = self.__sourceTree.findItems("*", QtCore.Qt.MatchWildcard | QtCore.Qt.MatchWrap | QtCore.Qt.MatchRecursive, 1)
        filterSearch = list(self.__sourceFilterSearch.text().lower().strip().split(' '))
        crawlerItems = []
        for treeItem in allTreeItems:
            # in case of collections we always want to hide the root item
            if not treeItem.parent():
                treeItem.setHidden(True)

            if not hasattr(treeItem, 'crawlers'):
                continue

            treeItem.setHidden(True)
            crawlerItems.append(treeItem)

            if treeItem.crawlers[0].var('type') not in visibleTypes:
                break

            for filterWord in filterSearch:
                if filterWord in str(treeItem.data(0, QtCore.Qt.EditRole)).lower():
                    treeItem.setHidden(False)
                    break

            if filterVarName:
                treeItem.setHidden(
                    not (treeItem.crawlers[0].var(filterVarName) in filterVarValues if filterVarName in treeItem.crawlers[0].varNames() and (not filterSearch or not treeItem.isHidden()) else False)
                )

        for crawlerItem in crawlerItems:
            if not crawlerItem.isHidden():
                parentItem = crawlerItem
                while parentItem:
                    parentItem = parentItem.parent()

                    if not parentItem:
                        break
                    parentItem.setHidden(False)

    def __updateIcon(self, item, crawler, columnIndex=0):
        """
        Set the icon based on the crawler for the tree item.
        """
        iconPath = crawler.tag('icon') if 'icon' in crawler.tagNames() else None
        if not iconPath:
            return

        if iconPath not in self.__iconCache:
            self.__iconCache[iconPath] = QtGui.QIcon(QtGui.QPixmap.fromImage(iconPath))

        item.setIcon(columnIndex, self.__iconCache[iconPath])

    def __camelCaseToSpaced(self, text):
        """
        Return the input camelCase string to spaced.
        """
        return text[0].upper() + re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>", text[1:])

    def __onSourceTreeItemCheckedChanged(self, currentItem):
        """
        Slot triggered when the check state of an item in the source tree is changed.
        """
        if not self.__sourceTree.selectionModel().selectedIndexes() or self.__ignoreCheckedEvents:
            return

        self.__ignoreCheckedEvents = True

        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            if hasattr(selectedItem, 'crawlers'):
                selectedItem.setCheckState(0, currentItem.checkState(0))

        self.__ignoreCheckedEvents = False

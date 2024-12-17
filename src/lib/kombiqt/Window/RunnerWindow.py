import os
import json
import getpass
import traceback
import functools
import weakref
from collections import OrderedDict
from Qt import QtCore, QtGui, QtWidgets
from kombi.TaskHolder.Loader import Loader
from kombi.TaskHolder.Dispatcher import Dispatcher
from kombi.Task import TaskValidationError
from kombi.Element import Element, ElementContext
from kombi.Element.Fs import FsElement
from kombi.Template import Template
from ..Widget.ExecutionSettingsWidget import ExecutionSettingsWidget
from ..Widget.DispatcherListWidget import DispatcherListWidget
from ..Widget.ComboBoxInputDialog import ComboBoxInputDialog
from ..Widget.ElementsLevelNavigationWidget import ElementsLevelNavigationWidget
from ..Widget.RunTaskHoldersWidget import RunTaskHoldersWidget
from ..Resource import Resource
from ..Widget.ImageElementViewer import ImageElementViewer

class RunnerWindow(QtWidgets.QMainWindow):
    """
    Basic graphical interface to pick files to run through a kombi configuration.
    """

    preRenderElements = QtCore.Signal(list)
    __viewModes = ["group", "flat"]
    __pickerLocation = os.environ.get('KOMBI_GUI_PICKER_LOCATION', '')
    __overridePreviousSelectedLocation = None

    def __init__(self, taskHolders, rootElement=None, customHeader='', **kwargs):
        """
        Create a Kombi app.
        """
        super(RunnerWindow, self).__init__(**kwargs)

        self.setStyleSheet(Resource.stylesheet())

        self.__taskHolders = taskHolders

        self.__configurationDirectory = ""
        self.__uiHintSourceColumns = []
        self.__customHeader = customHeader
        self.__verticalSourceScrollBarLatestPos = 0
        self.__showVars = False
        self.__showTags = False
        self.__uiHintGlobRecursively = False
        self.__ignoreCheckedEvents = False
        self.__checkableState = None
        self.__rootElements = []
        self.__buildWidgets()

        # task holders
        assert isinstance(taskHolders, (list, tuple)), "Invalid task holder list!"

        self.__updateSourceColumns(self.__taskHolders)
        self.__onRefreshSourceDir()

        if self.__taskHolders and 'configDirectory' in self.__taskHolders[0].varNames():
            self.__configurationDirectory = self.__taskHolders[0].var('configDirectory')
            self.setWindowTitle('Kombi ({0})'.format(self.__configurationDirectory))

        self.updateSource(rootElement)

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

    def updateSource(self, rootElement):
        """
        Update the source tree.
        """
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.__onUpdateSource(rootElement)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def __onUpdateSource(self, rootElement):
        """
        Update the source tree.
        """
        self.__sourceTree.clear()
        self.__sourceFilterMenu.clear()
        self.__sourceOverrides = {}

        if rootElement is None:
            return

        if self.__elementsLevelNavigationWidget.elements():
            self.__rootElements = self.__elementsLevelNavigationWidget.elements()

        try:
            index = self.__rootElements.index(rootElement)
        except ValueError:
            self.__rootElements = [rootElement]
        else:
            del self.__rootElements[index + 1:]

        self.__elementsLevelNavigationWidget.setElements(self.__rootElements)

        # we want to list in the interface only the element types used by the main tasks
        filterTypes = []
        filterDefaultTypes = ['directory']
        skipSourceStep = False
        self.__splitter.setOrientation(QtCore.Qt.Horizontal)
        self.__executionSettingsEmptyMessage = ''
        for taskHolder in self.__taskHolders:
            if '__uiHintShowPreview' in taskHolder.varNames() and taskHolder.var('__uiHintShowPreview'):
                self.__onToggleImageViewer(True)

            if '__uiHintTitle' in taskHolder.varNames():
                self.__logo.setTextFormat(QtCore.Qt.RichText)
                self.__logo.setText("<b><big><big> {}".format(taskHolder.var('__uiHintTitle')))

            if '__uiHintIconSize' in taskHolder.varNames():
                iconSize = taskHolder.var('__uiHintIconSize')
                self.__sourceTree.setIconSize(QtCore.QSize(iconSize, iconSize))

            if '__uiHintDispatcher' in taskHolder.varNames():
                self.__selectedDispatcher.selectDispatcher(taskHolder.var('__uiHintDispatcher'))

            if '__uiHintFilterDefaultTypes' in taskHolder.varNames():
                filterDefaultTypes = taskHolder.var('__uiHintFilterDefaultTypes')

            if '__uiHintGlobRecursively' in taskHolder.varNames():
                self.__uiHintGlobRecursively = taskHolder.var('__uiHintGlobRecursively')

            if '__uiHintBottomExecutionSettings' in taskHolder.varNames() and taskHolder.var('__uiHintBottomExecutionSettings'):
                self.__splitter.setOrientation(QtCore.Qt.Vertical)
                self.__executionSettingsAreaWidget.setVisible(True)
                self.refreshExecutionSettings()
                if '__uiHintBottomExecutionSettingsEmptyMessage' in taskHolder.varNames():
                    self.__executionSettingsEmptyMessage = taskHolder.var('__uiHintBottomExecutionSettingsEmptyMessage')

            elif '__uiHintSkipSourceStep' in taskHolder.varNames():
                skipSourceStep = taskHolder.var('__uiHintSkipSourceStep')

            if '__uiHintExecuteButtonLabel' in taskHolder.varNames():
                self.__executeButton.setText(taskHolder.var('__uiHintExecuteButtonLabel'))

            # if there is a task holder that does not have any type specified to it, then we display all elements by
            # passing an empty list to the filter
            if len(taskHolder.matcher().matchTypes()) == 0:
                filterTypes = []
                break

            filterTypes += taskHolder.matcher().matchTypes()
        filterTypes += filterDefaultTypes

        # globbing elements
        for taskHolder in filter(lambda x: '__uiHintCheckedByDefault' in x.varNames(), self.__taskHolders):
            self.__checkableState = taskHolder.var('__uiHintCheckedByDefault')
            self.__sourceOverrides = self.__loadSourceOverrides()

        self.__nextButton.setVisible(self.__checkableState is not None)
        self.__selectedDispatcher.setVisible(self.__checkableState is not None)

        if self.__checkableState is not None:
            self.__sourceTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        else:
            self.__sourceTree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        with ElementContext():
            elementList = []
            # filtering the result of the glob, but now using the element matcher
            # this will match the variable types.
            for taskHolder in self.__taskHolders:
                for elementFound in rootElement.glob(filterTypes, recursive=self.__uiHintGlobRecursively):
                    if elementFound.var('type') not in filterDefaultTypes and not taskHolder.matcher().match(elementFound):
                        continue
                    # since we may have several task holders we need to only
                    # include the element once
                    if elementFound not in elementList:
                        elementList.append(elementFound)

            self.preRenderElements.emit(elementList)
            self.__updateSourceTreeElementList(elementList)
            self.__onSourceFiltersChanged()

        # forcing kombi to start at the execution settings (next) interface
        if skipSourceStep:
            self.refreshExecutionSettings()

    def refreshExecutionSettings(self, elements=None):
        """
        Update the execution settings.
        """
        checkedElements = self.__checkedElements() if elements is None else elements

        # applying overrides
        self.__applySourceOverrides(
            self.__loadSourceOverrides(),
            checkedElements
        )

        self.__executionSettingsAreaWidget.setVisible(True)
        self.__selectedDispatcher.setVisible(True)
        self.__sourceAreaWidget.setVisible(self.__splitter.orientation() == QtCore.Qt.Vertical)
        self.__executeButton.setEnabled(True)

        self.__nextButton.setVisible(False)
        self.__backButton.setVisible(self.__splitter.orientation() == QtCore.Qt.Horizontal)
        self.__executeButton.setVisible(True)

        self.__executionSettings.refresh(checkedElements, self.__taskHolders)

        if self.__executionSettings.topLevelItemCount() == 0:
            self.__executionSettings.addTopLevelItem(QtWidgets.QTreeWidgetItem(['']))
            self.__executionSettings.addTopLevelItem(QtWidgets.QTreeWidgetItem([self.__executionSettingsEmptyMessage]))

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
        self.__splitter = QtWidgets.QSplitter()

        sourceLayout = QtWidgets.QVBoxLayout()
        sourceLayout.setContentsMargins(0, 0, 0, 0)
        sourceControlMain = QtWidgets.QMainWindow()
        sourceBarLayout = QtWidgets.QHBoxLayout()

        self.__elementsLevelNavigationWidget = ElementsLevelNavigationWidget()
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
        self.__sourceViewModeButton = QtWidgets.QPushButton()
        self.__sourceViewModeButton.setToolTip('Changes the view mode')
        self.__sourceViewModeButton.setIcon(
            Resource.icon("icons/viewMode.png")
        )
        self.__sourceViewModeMenu = QtWidgets.QMenu(self.__sourceViewModeButton)
        self.__sourceViewModeButton.setMenu(self.__sourceViewModeMenu)

        # filter
        self.__sourceFilterButton = QtWidgets.QPushButton()
        self.__sourceFilterButton.setToolTip('Filters out specific element types')
        self.__sourceFilterButton.setIcon(
            Resource.icon("icons/filterView.png")
        )
        self.__sourceFilterMenu = QtWidgets.QMenu(self.__sourceFilterButton)
        self.__sourceFilterButton.setMenu(self.__sourceFilterMenu)

        # filter search
        self.__sourceFilterSearch = QtWidgets.QLineEdit("")
        self.__sourceFilterSearch.setPlaceholderText("Filter...")
        self.__sourceFilterSearch.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.__sourceFilterSearch.setClearButtonEnabled(True)
        self.__sourceFilterSearch.setFixedWidth(150)

        self.__sourceDirButton.clicked.connect(self.__onSelectSourceDir)
        self.__sourceRefreshButton.clicked.connect(functools.partial(self.__onRefreshSourceDir, True))
        self.__elementsLevelNavigationWidget.levelClicked.connect(self.updateSource)
        self.__sourceFilterSearchTimer = QtCore.QTimer()
        self.__sourceFilterSearchTimer.setSingleShot(True)
        self.__sourceFilterSearchTimer.timeout.connect(self.__onSourceFiltersChanged)
        self.__sourceFilterSearch.textChanged.connect(self.__onSourceFilterSearch)

        sourceBarLayout.addWidget(self.__sourceDirButton)
        sourceBarLayout.addWidget(self.__elementsLevelNavigationWidget)
        sourceBarLayout.addWidget(self.__sourceRefreshButton)

        # image viewer
        self.__imageElementViewer = QtWidgets.QDockWidget("Preview")
        self.__imageElementViewer.setMinimumWidth(300)
        self.__imageElementViewer.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)

        self.__imageElementViewer.setWidget(ImageElementViewer([]))
        self.__imageElementViewer.setVisible(False)

        imageViewerButton = QtWidgets.QPushButton()
        imageViewerButton.setToolTip('Toggles the display of the preview panel')
        imageViewerButton.setIcon(
            Resource.icon("icons/imageViewer.png")
        )

        sourceControlMain.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.__imageElementViewer)
        sourceBarLayout.addWidget(imageViewerButton)

        imageViewerButton.clicked.connect(self.__onToggleImageViewer)

        sourceBarLayout.addWidget(self.__sourceFilterButton)
        sourceBarLayout.addWidget(self.__sourceViewModeButton)
        sourceBarLayout.addWidget(self.__sourceFilterSearch)

        sourceLayout.addLayout(sourceBarLayout)

        self.__sourceAreaWidget = QtWidgets.QWidget()
        self.__sourceAreaWidget.setLayout(sourceLayout)

        executionSettingsLayout = QtWidgets.QVBoxLayout()
        executionSettingsLayout.setContentsMargins(0, 0, 0, 0)

        self.__nextButton = QtWidgets.QPushButton("Next")
        self.__nextButton.setIcon(
            Resource.icon("icons/next.png")
        )
        self.__nextButton.clicked.connect(lambda x: self.refreshExecutionSettings())

        self.__backButton = QtWidgets.QPushButton("Back")
        self.__backButton.setIcon(
            Resource.icon("icons/back.png")
        )
        self.__backButton.setVisible(False)
        self.__backButton.clicked.connect(self.__onBack)

        self.__executionSettingsAreaWidget = QtWidgets.QWidget()
        self.__executionSettingsAreaWidget.setVisible(False)
        self.__executionSettingsAreaWidget.setLayout(executionSettingsLayout)

        self.__selectedDispatcher = DispatcherListWidget()

        self.__splitter.addWidget(self.__sourceAreaWidget)
        self.__splitter.addWidget(self.__executionSettingsAreaWidget)

        self.__sourceTree = self.__treeWidget([""])
        self.__sourceTree.itemChanged.connect(self.__onSourceTreeItemCheckedChanged)
        self.__sourceTree.itemSelectionChanged.connect(self.__onSourceTreeSelectionChanged)
        self.__sourceTree.customContextMenuRequested.connect(self.__onSourceTreeContextMenu)
        self.__sourceTree.itemDoubleClicked.connect(self.__onSourceTreeDoubleClick)
        self.__sourceTree.setIconSize(QtCore.QSize(32, 32))

        self.__executionSettings = ExecutionSettingsWidget()

        sourceControlMain.setCentralWidget(self.__sourceTree)

        sourceLayout.addWidget(sourceControlMain)
        executionSettingsLayout.addWidget(self.__executionSettings)

        # header
        headerLayout = QtWidgets.QHBoxLayout()
        centralWidget.layout().addLayout(headerLayout)

        self.__logo = QtWidgets.QLabel()
        if self.__customHeader:
            self.__logo.setTextFormat(QtCore.Qt.RichText)
            self.__logo.setText(self.__customHeader)
        else:
            logoFilePath = "icons/header.png"
            if '__uiHintLogo' in self.__taskHolders[0].varNames() and self.__taskHolders[0].var('__uiHintLogo'):
                logoFilePath = self.__taskHolders[0].var('__uiHintLogo')
                if not os.path.isabs(logoFilePath):
                    logoFilePath = os.path.realpath(os.path.join(self.__taskHolders[0].var('configDirectory'), logoFilePath))

            self.__logo.setPixmap(Resource.pixmap(logoFilePath).scaledToHeight(48, QtCore.Qt.SmoothTransformation))
        self.__logo.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        headerLayout.addWidget(self.__logo)
        headerLayout.addStretch()

        centralWidget.layout().addWidget(self.__splitter)
        buttonLayout = QtWidgets.QHBoxLayout()
        centralWidget.layout().addLayout(buttonLayout)

        self.__executeButton = QtWidgets.QPushButton('Execute')
        self.__executeButton.setVisible(False)
        self.__executeButton.setToolTip('Performs the tasks')
        self.__executeButton.clicked.connect(self.__onPerformTasks)

        buttonLayout.addWidget(self.__selectedDispatcher)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.__backButton)
        buttonLayout.addWidget(self.__nextButton)
        buttonLayout.addWidget(self.__executeButton)

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

    def __onPerformTasks(self):
        """
        Slog triggered by the run button.
        """
        dispatcher = Dispatcher.create(self.__selectedDispatcher.selectedDispatcher())
        self.__executionSettings.execute(
            dispatcher,
            showOutput=False,
            showDispatchedMessage=True
        )

    def __onSourceTreeSelectionChanged(self):
        """
        Slot called when selection changes on the source tree.
        """
        elements = []
        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            if not hasattr(selectedItem, 'elements'):
                continue
            for element in selectedItem.elements:
                elements.append(element)

        if self.__splitter.orientation() == QtCore.Qt.Vertical:
            self.refreshExecutionSettings(elements)

        if not (self.__imageElementViewer and self.__imageElementViewer.isVisible()):
            return

        self.__imageElementViewer.widget().setElements(elements)

    def __onToggleImageViewer(self, forceVisibility=False):
        """
        Slot triggered when the image preview button is pressed.
        """
        self.__imageElementViewer.setVisible(not self.__imageElementViewer.isVisible() or forceVisibility)

        if self.__imageElementViewer.isVisible() or forceVisibility:
            self.__imageElementViewer.parent().resizeDocks([self.__imageElementViewer], [400], QtCore.Qt.Horizontal)
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
        # the options properly inside of the execution settings
        if not len(columns):
            columns.append(' ')

        if columns != self.__uiHintSourceColumns:
            self.__uiHintSourceColumns = columns
            header = QtWidgets.QTreeWidgetItem(
                [''] + list(map(lambda x: Template.runProcedure('camelcasetospaced', x), self.__uiHintSourceColumns))
            )

            self.__sourceTree.setHeaderItem(
                header
            )

    def __updateSourceTreeElementList(self, elementList):
        """
        Update the elements displayed in the source tree.
        """
        elementTypes = set()
        elementTags = {}

        # workaround necessary to improve the rendering speed
        self.__sourceTree.setVisible(False)

        # group
        if self.__checkedViewMode == "Group":
            groupedElements = self.__groupElements(elementList)

            for groupName in groupedElements.keys():
                if groupName:
                    parent = QtWidgets.QTreeWidgetItem(self.__sourceTree)
                    self.__updateIcon(parent, groupedElements[groupName][0])
                    parent.elements = list(groupedElements[groupName])

                    # visible data
                    visibleGroupName = groupName + '   '
                    if visibleGroupName.startswith(os.sep):
                        visibleGroupName = visibleGroupName[1:]

                    parent.setData(0, QtCore.Qt.EditRole, visibleGroupName)

                    # adding column information
                    self.__addSourceTreeColumnData(groupedElements[groupName][0], parent, groupedElements[groupName])

                    if self.__checkableState is not None:
                        parent.setFlags(parent.flags() | QtCore.Qt.ItemIsUserCheckable)
                        parent.setCheckState(0, QtCore.Qt.Checked if self.__checkableState else QtCore.Qt.Unchecked)

                    for element in groupedElements[groupName]:
                        self.__createSourceTreeChildItem(
                            element,
                            parent,
                            elementTypes,
                            elementTags
                        )

                else:
                    for element in groupedElements[groupName]:
                        child = self.__createSourceTreeChildItem(
                            element,
                            self.__sourceTree,
                            elementTypes,
                            elementTags
                        )

                        if self.__checkableState is not None:
                            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                            child.setCheckState(0, QtCore.Qt.Checked if self.__checkableState else QtCore.Qt.Unchecked)

                        self.__addSourceTreeColumnData(element, child)

        # flat
        else:
            for element in elementList:

                # only testing with the first element when grouped
                if isinstance(element, list):
                    element = element[0]

                child = self.__createSourceTreeChildItem(element, self.__sourceTree, elementTypes, elementTags)

                if self.__checkableState is not None:
                    child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                    child.setCheckState(0, QtCore.Qt.Checked if self.__checkableState else QtCore.Qt.Unchecked)

                self.__addSourceTreeColumnData(element, child)

        # element info
        self.__elementInfoMenu = self.__sourceFilterMenu.addMenu('Element Info')

        # vars
        self.__showVarsAction = self.__elementInfoMenu.addAction('Vars')
        self.__showVarsAction.setCheckable(True)
        self.__showVarsAction.setChecked(self.__showVars)
        self.__showVarsAction.triggered.connect(self.__onFilterShowVars)

        # tags
        self.__showTagsAction = self.__elementInfoMenu.addAction('Tags')
        self.__showTagsAction.setCheckable(True)
        self.__showTagsAction.setChecked(self.__showTags)
        self.__showTagsAction.triggered.connect(self.__onFilterShowTags)

        # element types
        self.__elementTypesMenu = self.__sourceFilterMenu.addMenu('Element Types')

        allAction = self.__elementTypesMenu.addAction('ALL')
        allAction.triggered.connect(self.__onFilterSelectAll)

        noneAction = self.__elementTypesMenu.addAction('NONE')
        noneAction.triggered.connect(self.__onFilterSelectNone)
        self.__elementTypesMenu.addSeparator()

        # workaround to improve the performance of the rendering:
        # restoring the visibility of the widget
        self.__sourceTree.setVisible(True)

        for elementType in sorted(elementTypes):
            action = self.__elementTypesMenu.addAction(elementType)
            action.setCheckable(True)
            action.setChecked(True)
            action.changed.connect(self.__onSourceFiltersChanged)

        self.__sourceTree.resizeColumnToContents(0)

    def __groupElements(self, elements):
        """
        Return a dictionary containing the matched elements grouped.
        """
        groupedElements = OrderedDict()
        groupedElements[None] = []
        for elementList in Element.group(elements):
            for element in elementList:
                # group
                if self.__checkedViewMode == 'Group' and 'group' in element.tagNames():
                    groupName = element.tag('group')
                    if groupName not in groupedElements:
                        groupedElements[groupName] = []

                    groupedElements[groupName].append(element)

                # flat
                else:
                    groupedElements[None].append(element)

        return groupedElements

    def __treeWidget(self, columns=[]):
        """
        Return a tree widget used by source and execution settings.
        """
        sourceTree = QtWidgets.QTreeWidget()
        sourceTree.setAlternatingRowColors(True)

        sourceTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        sourceTree.setSelectionBehavior(QtWidgets.QTreeWidget.SelectItems)
        sourceTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        header = QtWidgets.QTreeWidgetItem(columns)
        sourceTree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        sourceTree.setHeaderItem(header)

        return sourceTree

    def __checkedElements(self):
        """
        Return a list of checked elements in the source tree.
        """
        totalRows = self.__sourceTree.model().rowCount()
        result = []
        for i in range(totalRows):
            self.__sourceTree.model().index(i, 0)
            item = self.__sourceTree.topLevelItem(i)

            # collections
            if not hasattr(item, 'elements'):
                for childIndex in range(item.childCount()):
                    childItem = item.child(childIndex)
                    if childItem.checkState(0) and hasattr(childItem, 'elements'):
                        result.extend(childItem.elements)

            # root items
            elif item.checkState(0) and hasattr(item, 'elements'):
                result.extend(item.elements)

        return list(map(lambda x: x.clone(), result))

    def __sourceOverridesConfig(self):
        """
        Return the full path about the location for the override files.
        """
        return os.path.join(
            self.__configurationDirectory,
            "overrides",
            "{}.json".format(
                getpass.getuser()
            )
        )

    def __loadSourceOverrides(self):
        """
        Load element overrides in the source tree.
        """
        result = {}

        if os.path.exists(self.__sourceOverridesConfig()):
            with open(self.__sourceOverridesConfig()) as sourceFile:
                result = json.load(sourceFile)
                if result and "overrides" in result:
                    result = result["overrides"]

        return result

    def __applySourceOverrides(self, overrides, elements):
        """
        Apply overrides overrides on the source tree.
        """
        if not overrides:
            return

        with ElementContext():
            def __allElements(childElement):
                fullPath = childElement.var('fullPath')
                if fullPath in overrides:
                    for varName, varValue in overrides[fullPath].items():
                        childElement.setVar(
                            varName,
                            varValue,
                            varName in childElement.contextVarNames()
                        )

                if not childElement.isLeaf():
                    for element in childElement.children():
                        __allElements(element)

            for element in elements:
                __allElements(element)

    def __addSourceTreeColumnData(self, element, treeItem, groupedElements=None):
        """
        Add element information to a column in the source tree.
        """
        # adding column information
        for index, column in enumerate(self.__uiHintSourceColumns):

            hasOverride = False
            value = ''
            columnLabel = ''
            mixedValues = False
            for elementIndex, checkElement in enumerate(groupedElements if groupedElements else [element]):
                currentValue = ''
                if checkElement.var('fullPath') in self.__sourceOverrides and column in self.__sourceOverrides[checkElement.var('fullPath')]:
                    currentValue = self.__sourceOverrides[checkElement.var('fullPath')][column]
                    hasOverride = True
                if column in checkElement.varNames():
                    if not hasOverride:
                        currentValue = checkElement.var(column)

                if currentValue != value and elementIndex:
                    mixedValues = True
                    break
                value = currentValue

            columnLabel = ('mixed' if mixedValues else str(value)) + '   '

            # creating custom widget to show the presets
            if '{}.button'.format(column) in element.tagNames() or '{}.icon'.format(column) in element.tagNames():
                columnButton = QtWidgets.QPushButton(self)
                if '{}.icon'.format(column) in element.tagNames():
                    columnButton.setIcon(Resource.icon(element.tag('{}.icon'.format(column))))
                columnButton.setObjectName('columnButton')
                columnButton.setText(str(value))
                columnButton.setFixedSize(columnButton.minimumSizeHint())
                columnButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
                if '{}.button'.format(column) in element.tagNames():
                    columnButton.clicked.connect(functools.partial(self.__onColumnButton, weakref.ref(treeItem), element.tag('{}.button'.format(column))))
                self.__sourceTree.setItemWidget(treeItem, index + 1, columnButton)

            # creating custom widget to show the presets
            elif '{}.presets'.format(column) in element.tagNames() or value is not None and isinstance(value, bool):
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

            elif value == '' and column in element.varNames() and \
                    (not element.tag('{}.allowEmpty'.format(column)) if '{}.allowEmpty'.format(column) in element.tagNames() else True):
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

    def __createSourceTreeChildItem(self, element, parent, elementTypes, elementTags):
        """
        Create a new child item in the source tree.
        """
        child = QtWidgets.QTreeWidgetItem(parent)
        child.elements = [element]
        self.__updateIcon(child, element)

        # visible data
        child.setData(0, QtCore.Qt.EditRole, element.var('baseName') + '   ')
        self.__addSourceTreeColumnData(element, child)

        elementTypes.add(element.var('type'))

        if self.__showVars:
            variables = QtWidgets.QTreeWidgetItem(child)
            variables.setData(
                0,
                QtCore.Qt.EditRole,
                'vars'
            )
            for varName in sorted(element.varNames()):
                if varName in ['path']:
                    continue

                variablesChild = QtWidgets.QTreeWidgetItem(variables)
                variablesChild.setData(
                    0,
                    QtCore.Qt.EditRole,
                    '{0}={1}'.format(varName, element.var(varName))
                )

        if self.__showTags:
            tags = QtWidgets.QTreeWidgetItem(child)
            tags.setData(
                0,
                QtCore.Qt.EditRole,
                'tags'
            )

            for tagName in element.tagNames():
                tagValue = element.tag(tagName)
                if not isinstance(tagValue, str):
                    continue

                if tagName not in elementTags:
                    elementTags[tagName] = set()
                elementTags[tagName].add(tagValue)

            for tagName in sorted(element.tagNames()):
                tagChild = QtWidgets.QTreeWidgetItem(tags)
                tagChild.setData(
                    0,
                    QtCore.Qt.EditRole,
                    '{0}={1}'.format(tagName, element.tag(tagName))
                )

        return child

    def __onBack(self):
        """
        Slot triggered when back button is triggered.
        """
        self.__selectedDispatcher.setVisible(False)
        self.__backButton.setVisible(False)
        self.__nextButton.setVisible(True)
        self.__executeButton.setVisible(False)
        self.__sourceAreaWidget.setVisible(True)
        self.__executionSettingsAreaWidget.setVisible(False)

    def __onChangeView(self):
        """
        Slot triggered when change view mode is triggered.
        """
        checkedAction = self.__viewModeActionGroup.checkedAction()
        if checkedAction and checkedAction.text() != self.__checkedViewMode:
            self.__checkedViewMode = self.__viewModeActionGroup.checkedAction().text()
            self.__onRefreshSourceDir()

    def __onColumnButton(self, treeItemWeakRef, callableName):
        """
        Slot triggered when the column button is clicked.
        """
        elements = treeItemWeakRef().elements

        # executing callable
        for index, element in enumerate(elements):
            if hasattr(element, callableName):
                try:
                    getattr(elements[0], callableName)(index, len(elements))
                except Exception as err:
                    traceback.print_exc()

                    QtWidgets.QMessageBox.critical(
                        None,
                        "Kombi",
                        "Error during the execution {}:\n\n{}".format(str(element), str(err)),
                        QtWidgets.QMessageBox.Ok
                    )

                    raise err
            else:
                QtWidgets.QMessageBox.critical(
                    None,
                    "Kombi",
                    'Could not find callable "{0}" in element "{1}"'.format(
                        callableName,
                        str(elements[0].var('type'))
                    ),
                    QtWidgets.QMessageBox.Ok
                )

    def __onSourceTreePresetsClicked(self, treeItemWeakRef, columnIndex):
        """
        Slot triggered when the preset arrow button is clicked.
        """
        currentIndex = self.__sourceTree.indexFromItem(treeItemWeakRef(), columnIndex)

        # resetting the selection in case the clicked item is not part of
        # the selection
        if currentIndex not in self.__sourceTree.selectionModel().selectedIndexes():
            self.__sourceTree.selectionModel().select(currentIndex, QtCore.QItemSelectionModel.SelectCurrent)

        self.__onChangeElementValue()

    def __onSourceTreeDoubleClick(self, item):
        """
        Slot triggered when an item is double clicked on the source tree.
        """
        if not item.elements[0].isLeaf():
            self.__rootElements.append(item.elements[0])
            self.updateSource(item.elements[0])

    def __onSourceTreeContextMenu(self, point=None):
        """
        Slot triggered when context menu from source tree is triggered.
        """
        self.__sourceTree.resizeColumnToContents(0)

        selectedIndexes = self.__sourceTree.selectionModel().selectedIndexes()
        if not selectedIndexes:
            return

        selectedColumn = selectedIndexes[0].column()
        menu = QtWidgets.QMenu(self)
        if selectedColumn == 0:
            elements = self.__selectedElements()
            for index, taskHolder in enumerate(self.__taskHolders):
                filteredElements = []
                for element in elements:
                    if not taskHolder.matcher().match(element):
                        continue
                    filteredElements.append(element)

                if not filteredElements:
                    continue

                try:
                    taskHolder.task().validate(filteredElements)
                except Exception as err:
                    if not isinstance(err, TaskValidationError):
                        traceback.print_exc()
                else:
                    taskName = Template.runProcedure('camelcasetospaced', taskHolder.task().metadata('name'))
                    if taskHolder.task().hasMetadata('ui.task.showExecutionSettings') and not taskHolder.task().metadata('ui.task.showExecutionSettings'):
                        pass
                    else:
                        taskName += ' ...'
                    action = menu.addAction(taskName)
                    action.triggered.connect(functools.partial(self.__onRunTaskHolder, index, filteredElements))
        elif self.__checkableState is not None:
            action = menu.addAction('Override Value')
            action.triggered.connect(self.__onChangeElementValue)

            action = menu.addAction('Reset Value')
            action.triggered.connect(self.__onResetElementValue)

        if len(menu.actions()):
            menu.exec_(self.__sourceTree.mapToGlobal(point) if point is not None else QtGui.QCursor.pos())

    def __onRunTaskHolder(self, index, elements):
        """
        Slog triggered by the context menu action to run the task holders.
        """
        if RunTaskHoldersWidget.run([self.__taskHolders[index]], elements, parent=self):
            self.__onRefreshSourceDir(force=True)

    def __onChangeElementValue(self):
        """
        Slot triggered when an override in the source tree is triggered.
        """
        value = None
        overrides = dict(self.__sourceOverrides)

        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            elements = []
            if hasattr(selectedItem, 'elements'):
                elements = selectedItem.elements[:]
            if not elements:
                continue

            selectedColumn = selectedIndex.column()
            columnName = self.__uiHintSourceColumns[selectedColumn - 1]

            hintValue = ""
            fileChooserName = '{}.fileChooserOnOverride'.format(columnName)
            showFileChooser = fileChooserName in elements[0].tagNames() and elements[0].tag(fileChooserName)
            if columnName in elements[0].varNames():
                hintValue = elements[0].var(columnName)

            if value is None:
                allPresets = []

                if hintValue is not None and isinstance(hintValue, bool):
                    allPresets.append('True')
                    allPresets.append('False')
                else:
                    presetsName = '{}.presets'.format(columnName)
                    for elementItem in elements:
                        if presetsName not in elementItem.tagNames():
                            continue

                        for presetValue in elementItem.tag(presetsName):
                            if presetValue not in allPresets:
                                allPresets.append(presetValue)

                    if len(elements) > 1:
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
                        if '{}.fileChooserOnOverrideAllowedExt'.format(columnName) in elements[0].tagNames():
                            ext = "{ext} (*.{ext})".format(
                                ext=elements[0].tag('{}.fileChooserOnOverrideAllowedExt'.format(columnName))
                            )

                        value = QtWidgets.QFileDialog.getOpenFileName(
                            self,
                            "Select a file to override: {}".format(
                                elements[0].var('baseName')
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

            for elementItem in elements:
                elementFullPath = elementItem.var('fullPath')

                # skipping the same value that is currently set in the element
                if columnName in elementItem.varNames() and value == elementItem.var(columnName):
                    if elementFullPath in overrides and columnName in overrides[elementFullPath]:
                        del overrides[elementFullPath][columnName]
                    continue

                # adding
                if elementFullPath not in overrides:
                    overrides[elementFullPath] = {}

                overrides[elementFullPath][columnName] = value

        if not os.path.exists(os.path.dirname(self.__sourceOverridesConfig())):
            os.mkdir(os.path.dirname(self.__sourceOverridesConfig()))

        with open(self.__sourceOverridesConfig(), 'w') as sourceFile:
            data = {
                "overrides": overrides
            }

            json.dump(data, sourceFile, indent=4)

        if value is not None:
            self.__onRefreshSourceDir()

    def __onResetElementValue(self):
        """
        Slot triggered when an override in the source tree is removed.
        """
        overrides = dict(self.__sourceOverrides)

        selectedElements = set()
        columnNames = set()
        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            elements = []
            if hasattr(selectedItem, 'elements'):
                elements = selectedItem.elements[:]
            if not elements:
                continue

            selectedColumn = selectedIndex.column()
            columnName = self.__uiHintSourceColumns[selectedColumn - 1]

            selectedElements.update(elements)
            columnNames.add(columnName)

        for fullPath in map(lambda x: x.var('fullPath'), selectedElements):
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
                    "overrides": overrides
                }
                json.dump(data, sourceFile, indent=4)

            self.__onRefreshSourceDir()

    def __selectedElements(self):
        """
        Return a list of selected elements.
        """
        selectedElements = set()
        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            elements = []
            if hasattr(selectedItem, 'elements'):
                elements = selectedItem.elements[:]
            if not elements:
                continue

            selectedElements.update(elements)

        return list(selectedElements)

    def __onSelectSourceDir(self):
        """
        Slot triggered when select source button is triggered.
        """
        self.__verticalSourceScrollBarLatestPos = 0
        currentDir = self.__pickerLocation
        if self.__rootElements and isinstance(self.__rootElements[0], FsElement):
            currentDir = self.__rootElements[0].var('fullPath')

        selectedDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select source directory",
            currentDir,
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if selectedDirectory:
            self.updateSource(FsElement.createFromPath(selectedDirectory))

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
            for rootElement in self.__rootElements:
                rootElement.flushChildrenCache()

        if self.__rootElements:
            self.updateSource(self.__rootElements[-1])

        # reapplying the state
        for index in range(self.__sourceTree.topLevelItemCount()):
            item = self.__sourceTree.topLevelItem(index)
            key = (index, item.text(0))

            if key in treeData:
                if self.__checkableState is not None and bool(item.flags() & QtCore.Qt.ItemIsUserCheckable):
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
        for action in self.__elementTypesMenu.actions():
            action.setChecked(False)

    def __onFilterSelectAll(self):
        """
        Slot triggered when select all filter is triggered.
        """
        for action in self.__elementTypesMenu.actions():
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
        for action in self.__elementTypesMenu.actions():
            if action.isChecked():
                visibleTypes.append(action.text())

        allTreeItems = self.__sourceTree.findItems("*", QtCore.Qt.MatchWildcard | QtCore.Qt.MatchWrap | QtCore.Qt.MatchRecursive, 1)
        filterSearch = list(self.__sourceFilterSearch.text().lower().strip().split(' '))
        elementItems = []
        for treeItem in allTreeItems:
            # in case of collections we always want to hide the root item
            if not treeItem.parent():
                treeItem.setHidden(True)

            if not hasattr(treeItem, 'elements'):
                continue

            treeItem.setHidden(True)
            elementItems.append(treeItem)

            if treeItem.elements[0].var('type') not in visibleTypes:
                continue

            for filterWord in filterSearch:
                if filterWord in str(treeItem.data(0, QtCore.Qt.EditRole)).lower():
                    treeItem.setHidden(False)
                    break

        for elementItem in elementItems:
            if not elementItem.isHidden():
                parentItem = elementItem
                while parentItem:
                    parentItem = parentItem.parent()

                    if not parentItem:
                        break
                    parentItem.setHidden(False)

    def __updateIcon(self, item, element, columnIndex=0):
        """
        Set the icon based on the element for the tree item.
        """
        iconPath = element.tag('icon') if 'icon' in element.tagNames() else None
        if not iconPath:
            return

        item.setIcon(columnIndex, Resource.icon(iconPath))

    def __onSourceTreeItemCheckedChanged(self, currentItem):
        """
        Slot triggered when the check state of an item in the source tree is changed.
        """
        if not self.__sourceTree.selectionModel().selectedIndexes() or self.__ignoreCheckedEvents:
            return

        self.__ignoreCheckedEvents = True

        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedItem = self.__sourceTree.itemFromIndex(selectedIndex)

            if hasattr(selectedItem, 'elements'):
                selectedItem.setCheckState(0, currentItem.checkState(0))

        self.__ignoreCheckedEvents = False

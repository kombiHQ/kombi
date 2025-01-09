import os
import functools
import traceback
from Qt import QtCore, QtWidgets
from kombi.TaskHolder.Loader import Loader
from kombi.TaskHolder.Dispatcher import Dispatcher
from kombi.Element import ElementContext
from kombi.Element.Fs import FsElement
from ..Resource import Resource
from ..Element import ElementListWidget
from ..Widget.ExecutionSettingsWidget import ExecutionSettingsWidget
from ..Widget.DispatcherListWidget import DispatcherListWidget
from ..Widget.ElementsLevelNavigationWidget import ElementsLevelNavigationWidget
from ..Widget.ImageElementViewer import ImageElementViewer
from ..Widget.ScriptEditorWidget import ScriptEditorWidget

class RunnerWindow(QtWidgets.QMainWindow):
    """
    Basic graphical interface to pick files to run through a kombi configuration.
    """

    preRenderElements = QtCore.Signal(list)
    __pickerLocation = os.environ.get('KOMBI_GUI_PICKER_LOCATION', '')

    def __init__(self, taskHolders, rootElement=None, customHeader='', **kwargs):
        """
        Create a Kombi app.
        """
        super(RunnerWindow, self).__init__(**kwargs)

        self.setStyleSheet(Resource.stylesheet())

        self.__taskHolders = taskHolders
        self.__customHeader = customHeader
        self.__uiHintGlobRecursively = False
        self.__rootElements = []
        self.__buildWidgets()

        self.__sourceFilterMenu = QtWidgets.QMenu(self.__sourceFilterButton)
        self.__sourceFilterButton.setMenu(self.__sourceFilterMenu)

        # vars
        self.__showVarsAction = self.__sourceFilterMenu.addAction('Vars')
        self.__showVarsAction.setCheckable(True)
        self.__showVarsAction.setChecked(self.__sourceTree.showVars())
        self.__showVarsAction.triggered.connect(self.__onFilterShowVars)

        # tags
        self.__showTagsAction = self.__sourceFilterMenu.addAction('Tags')
        self.__showTagsAction.setCheckable(True)
        self.__showTagsAction.setChecked(self.__sourceTree.showTags())
        self.__showTagsAction.triggered.connect(self.__onFilterShowTags)

        # task holders
        assert isinstance(taskHolders, (list, tuple)), "Invalid task holder list!"

        self.__sourceTree.refresh()

        if self.__taskHolders and 'configDirectory' in self.__taskHolders[0].varNames():
            self.setWindowTitle('Kombi ({0})'.format(self.__taskHolders[0].var('configDirectory')))

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

    def gotoPath(self, fullPath, selectLeaf=True):
        """
        Change the navigation to the input path.
        """
        if selectLeaf:
            self.__elementsLevelNavigationWidget.gotoPath(os.path.dirname(fullPath))

            baseName = os.path.basename(fullPath)
            for index in range(self.__sourceTree.topLevelItemCount()):
                item = self.__sourceTree.topLevelItem(index)
                for element in item.elements:
                    if element.var('name') != baseName:
                        continue
                    self.__sourceTree.setCurrentItem(item, 0)
                    break
        else:
            self.__elementsLevelNavigationWidget.gotoPath(fullPath)

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
        self.__closeAfterExecution = False
        self.__splitter.setOrientation(QtCore.Qt.Horizontal)
        self.__executionSettingsEmptyMessageLabel.setText('')
        self.__executionSettingsEmptyMessageLabel.setVisible(False)
        self.__sourceTree.setup(self.__taskHolders)
        for taskHolder in self.__taskHolders:
            if '__uiHintCloseAfterExecution' in taskHolder.varNames():
                self.__closeAfterExecution = taskHolder.var('__uiHintCloseAfterExecution')

            if '__uiHintShowPreview' in taskHolder.varNames() and taskHolder.var('__uiHintShowPreview'):
                self.__onToggleImageViewer(True)

            if '__uiHintTitle' in taskHolder.varNames():
                self.__logo.setTextFormat(QtCore.Qt.RichText)
                self.__logo.setText("<b><big><big> {}".format(taskHolder.var('__uiHintTitle')))

            if '__uiHintDispatcher' in taskHolder.varNames():
                self.__selectedDispatcher.selectDispatcher(taskHolder.var('__uiHintDispatcher'))

            if '__uiHintFilterDefaultTypes' in taskHolder.varNames():
                filterDefaultTypes = taskHolder.var('__uiHintFilterDefaultTypes')

            if '__uiHintGlobRecursively' in taskHolder.varNames():
                self.__uiHintGlobRecursively = taskHolder.var('__uiHintGlobRecursively')

            if '__uiHintBottomExecutionSettings' in taskHolder.varNames() and taskHolder.var('__uiHintBottomExecutionSettings'):
                self.__splitter.setOrientation(QtCore.Qt.Vertical)
                self.__executionSettingsAreaWidget.setVisible(True)
                if '__uiHintBottomExecutionSettingsEmptyMessage' in taskHolder.varNames():
                    self.__executionSettingsEmptyMessageLabel.setText(taskHolder.var('__uiHintBottomExecutionSettingsEmptyMessage'))
                self.refreshExecutionSettings()

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

        if filterTypes:
            filterTypes.extend(filterDefaultTypes)

        self.__nextButton.setVisible(self.__sourceTree.checkableState() is not None)
        self.__selectedDispatcher.setVisible(self.__sourceTree.checkableState() is not None)

        with ElementContext():
            elementList = []
            # filtering the result of the glob, but now using the element matcher
            # this will match the variable types.
            for elementFound in rootElement.glob(filterTypes, recursive=self.__uiHintGlobRecursively):
                for taskHolder in self.__taskHolders:
                    if elementFound.var('type') not in filterDefaultTypes and not taskHolder.matcher().match(elementFound):
                        continue
                    # since we may have several task holders we need to only
                    # include the element once
                    if elementFound not in elementList:
                        elementList.append(elementFound)

            self.preRenderElements.emit(elementList)
            self.__sourceTree.setElementList(elementList)

        # forcing kombi to start at the execution settings (next) interface
        if skipSourceStep:
            self.refreshExecutionSettings()

    def refreshExecutionSettings(self, elements=None):
        """
        Update the execution settings.
        """
        checkedElements = self.__sourceTree.checkedElements() if elements is None else elements

        self.__executionSettingsAreaWidget.setVisible(True)
        self.__selectedDispatcher.setVisible(True)
        self.__sourceAreaWidget.setVisible(self.__splitter.orientation() == QtCore.Qt.Vertical)
        self.__executeButton.setEnabled(True)

        self.__nextButton.setVisible(False)
        self.__backButton.setVisible(self.__splitter.orientation() == QtCore.Qt.Horizontal)
        self.__executeButton.setVisible(True)

        if self.__taskHolders and '__uiHintBottomExecutionSettings' in self.__taskHolders[0].varNames() and self.__taskHolders[0].var('__uiHintBottomExecutionSettings'):
            if not checkedElements and self.__rootElements:
                checkedElements = [self.__rootElements[-1]]
            self.__executionSettings.refresh(checkedElements, [self.__taskHolders[0]])
        else:
            self.__executionSettings.refresh(checkedElements, self.__taskHolders)

        if self.__executionSettings.topLevelItemCount() == 0:
            self.__executionSettingsEmptyMessageLabel.setVisible(True)
            self.__executionSettingsEmptyMessageLabel.setFixedSize(self.__executionSettingsEmptyMessageLabel.minimumSizeHint())
        else:
            self.__executionSettingsEmptyMessageLabel.setFixedSize(0, 0)

    def dispatcherWidget(self):
        """
        Return the dispatcher widget.
        """
        return self.__selectedDispatcher

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
        self.__scriptEditor = None
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

        self.__sourceDirButton.clicked.connect(self.__onSelectSourceDir)
        self.__elementsLevelNavigationWidget.levelClicked.connect(self.updateSource)
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

        scriptEditorButton = QtWidgets.QPushButton()
        scriptEditorButton.setToolTip('Toogles the display of the script editor')
        scriptEditorButton.setIcon(
            Resource.icon("icons/python.png")
        )
        scriptEditorButton.clicked.connect(self.__onToggleScriptEditor)

        sourceBarLayout.addWidget(self.__sourceFilterButton)
        sourceBarLayout.addWidget(self.__sourceViewModeButton)
        sourceBarLayout.addWidget(scriptEditorButton)

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

        self.__sourceTree = ElementListWidget()
        self.__sourceTree.itemSelectionChanged.connect(self.__onSourceTreeSelectionChanged)
        self.__sourceTree.itemDoubleClicked.connect(self.__onSourceTreeDoubleClick)
        self.__sourceTree.modifed.connect(self.__onForceRefresh)
        self.__sourceRefreshButton.clicked.connect(self.__onForceRefresh)

        self.__executionSettings = ExecutionSettingsWidget()
        sourceControlMain.setCentralWidget(self.__sourceTree)

        sourceLayout.addWidget(sourceControlMain)
        executionSettingsLayout.addWidget(self.__executionSettings)
        self.__executionSettingsEmptyMessageLabel = QtWidgets.QLabel('', self.__executionSettings)
        self.__executionSettingsEmptyMessageLabel.move(10, 10)
        self.__executionSettingsEmptyMessageLabel.setVisible(False)

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
        for viewMode in self.__sourceTree.viewModes:
            viewAction = self.__sourceViewModeMenu.addAction(viewMode.capitalize())
            viewAction.triggered.connect(functools.partial(self.__sourceTree.setViewMode, viewMode))
            self.__viewModeActionGroup.addAction(viewAction)

    def __onForceRefresh(self):
        """
        Refresh the running window.
        """
        for rootElement in self.__rootElements:
            rootElement.flushChildrenCache()

        if self.__rootElements:
            self.updateSource(self.__rootElements[-1])

        self.__sourceTree.refresh()

    def __onPerformTasks(self):
        """
        Slog triggered by the run button.
        """
        selectedDispatcher = self.__selectedDispatcher.selectedDispatcher()
        dispatcher = Dispatcher.create(selectedDispatcher)
        if self.__executionSettings.execute(dispatcher, showOutput=False, showDispatchedMessage=selectedDispatcher != 'runtime') and self.__closeAfterExecution:
            self.close()

    def __onSourceTreeSelectionChanged(self):
        """
        Slot called when selection changes on the source tree.
        """
        elements = self.__sourceTree.selectedElements()

        if self.__splitter.orientation() == QtCore.Qt.Vertical:
            self.refreshExecutionSettings(elements)

        if not (self.__imageElementViewer and self.__imageElementViewer.isVisible()):
            return

        self.__imageElementViewer.widget().setElements(elements)

    def __onToggleScriptEditor(self):
        """
        Slot triggered when the script editor button is pressed.
        """
        if self.__scriptEditor is None:
            self.__scriptEditor = ScriptEditorWidget()
            self.__splitter.addWidget(self.__scriptEditor)
            self.__scriptEditor.setVisible(True)
            return

        self.__scriptEditor.setVisible(not self.__scriptEditor.isVisible())

    def __onToggleImageViewer(self, forceVisibility=False):
        """
        Slot triggered when the image preview button is pressed.
        """
        self.__imageElementViewer.setVisible(not self.__imageElementViewer.isVisible() or forceVisibility)

        if self.__imageElementViewer.isVisible() or forceVisibility:
            self.__onSourceTreeSelectionChanged()

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

    def __onSourceTreeDoubleClick(self, item):
        """
        Slot triggered when an item is double clicked on the source tree.
        """
        if not item.elements[0].isLeaf():
            self.__rootElements.append(item.elements[0])
            self.updateSource(item.elements[0])

    def __onSelectSourceDir(self):
        """
        Slot triggered when select source button is triggered.
        """
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

    def __onFilterShowVars(self, *args):
        """
        Slot triggered when info show vars is triggered.
        """
        self.__sourceTree.setShowVars(self.__showVarsAction.isChecked())

    def __onFilterShowTags(self, *args):
        """
        Slot triggered when info show tags is triggered.
        """
        self.__sourceTree.setShowTags(self.__showTagsAction.isChecked())

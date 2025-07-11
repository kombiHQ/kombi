import os
import functools
import traceback
from Qt import QtCore, QtWidgets, QtGui
from kombi.TaskHolder.Loader import Loader
from kombi.Dispatcher import Dispatcher
from kombi.Element import Element, ElementContext
from kombi.Element.Fs import FsElement
from .PreferencesWindow import PreferencesWindow
from ..Resource import Resource
from ..Menu.TasksMenu import TasksMenu
from ..Widget import ElementListWidget, ElementsTreeWidgetItem
from ..Widget.ElementViewerWidget import ElementViewerWidget
from ..Widget.ElementLevelNavigationWidget import ElementLevelNavigationWidget
from ..Widget.TaskHolderListWidget import TaskHolderListWidget
from ..Widget.DispatcherListWidget import DispatcherListWidget
from ..Window.ScriptEditorWindow import ScriptEditorWindow
from ..OptionVisual import OptionVisual

class BrowserWindow(ScriptEditorWindow):
    """
    A graphical user interface for interacting with Kombi configurations.

    Signals:
    - preRenderElements: Emitted when the element list is about to be rendered.
    """

    preRenderElements = QtCore.Signal(list)
    __pickerLocation = os.environ.get('KOMBI_GUI_PICKER_LOCATION', '')

    def __init__(self, taskHolders, rootElement=None, customHeader='', viewMode='group', **kwargs):
        """
        Create a BrowserWindow object.
        """
        super().__init__(mainWidget=QtWidgets.QWidget(), **kwargs)

        self.setWindowTitle('Kombi')
        self.resize(1280, 720)

        self.setStyleSheet(Resource.stylesheet())

        self.__taskHolders = taskHolders
        self.__customHeader = customHeader
        self.__uiHintGlobRecursively = False
        self.__rootElements = []
        self.__buildWidgets()

        self.__elementListWidget.setViewMode(viewMode)

        # task holders
        assert isinstance(taskHolders, (list, tuple)), "Invalid task holder list!"

        self.__elementListWidget.refresh()

        if self.__taskHolders and 'configDirectory' in self.__taskHolders[0].varNames():
            self.setWindowTitle('Kombi ({0})'.format(self.__taskHolders[0].var('configDirectory')))

        self.setRootElement(rootElement)

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

    def elementListWidget(self):
        """
        Return the element list widget.
        """
        return self.__elementListWidget

    def elementsLevelNavigationWidget(self):
        """
        Return the elements level navigation widget.
        """
        return self.__elementsLevelNavigationWidget

    def gotoPath(self, fullPath, selectLeaf=True):
        """
        Change the navigation to the input path.
        """
        if selectLeaf:
            self.__elementsLevelNavigationWidget.gotoPath(os.path.dirname(fullPath))

            baseName = os.path.basename(fullPath)
            for index in range(self.__elementListWidget.topLevelItemCount()):
                item = self.__elementListWidget.topLevelItem(index)

                if not isinstance(item, ElementsTreeWidgetItem):
                    continue

                for element in item.elements():
                    if element.var('name') != baseName:
                        continue
                    self.__elementListWidget.setCurrentItem(item, 0)
                    break
        else:
            self.__elementsLevelNavigationWidget.gotoPath(fullPath)

    def rootElement(self):
        """
        Return the root element used to list the elements (None in case the root element has not been defined).
        """
        if self.__rootElements:
            return self.__rootElements[-1]
        return None

    def setRootElement(self, rootElement):
        """
        Set the root element, updating elements.
        """
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.__updateElementList(rootElement)

            if self.__infoPanel and self.__infoPanel.isVisible():
                self.__elementViewer.setElements([rootElement])
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def refreshTaskHolderList(self, elements=None):
        """
        Update the execution settings.
        """
        checkedElements = self.__elementListWidget.checkedElements() if elements is None else elements

        self.__executionSettingsAreaWidget.setVisible(True)
        self.__selectedDispatcher.setVisible(True)
        self.__sourceAreaWidget.setVisible(self.__splitter.orientation() == QtCore.Qt.Vertical)
        self.__executeButton.setEnabled(True)

        self.__nextButton.setVisible(False)
        self.__backButton.setVisible(self.__splitter.orientation() == QtCore.Qt.Horizontal)
        self.__executeButton.setVisible(True)

        if self.__taskHolders and self.__taskHolders[0].tag('uiHintBottomTaskHolderList', None):
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

        if self.__taskHolders[0].tag('uiHintExecuteImmediately', None):
            try:
                self.__executionSettingsAreaWidget.setVisible(False)
                self.__executeButton.setVisible(False)
                self.__backButton.setVisible(False)
                self.__sourceAreaWidget.setVisible(True)
                self.__executeButton.click()
            finally:
                self.__backButton.click()

    def dispatcherWidget(self):
        """
        Return the dispatcher widget.
        """
        return self.__selectedDispatcher

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

    @classmethod
    def run(cls, args):
        """
        Create a basic graphical interface to pick files to run through a kombi configuration.

        Example:
            kombi-gui <CONFIGURATION-DIRECTORY> [<INPUT-FILES-DIRECTORY>]
        """
        # getting configuration directory from the args
        configurationDirectory = ''
        if len(args) > 1:
            configurationDirectory = args[1]

        # otherwise from the environment
        elif 'KOMBIAPP_CONFIG_DIR' in os.environ:
            configurationDirectory = os.environ['KOMBIAPP_CONFIG_DIR']

        # showing configuration directory picker
        if not configurationDirectory:
            configurationDirectory = BrowserWindow.pickConfigurationDirectory(configurationDirectory)

        # loading task holders
        taskHolders = BrowserWindow.loadConfigurationTaskHolders(configurationDirectory)

        # source element path
        rootElement = None
        if len(args) > 2:
            rootElement = FsElement.createFromPath(args[2])
            # wrapping the leaf element a collection element, so it can be
            # displayed in the UI
            if rootElement.isLeaf():
                rootElement = Element.create([rootElement])

        browserWindow = cls(taskHolders, rootElement)
        return browserWindow

    def __updateElementList(self, rootElement):
        """
        Update the element list.
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
        self.__elementListWidget.setup(self.__taskHolders)
        for taskHolder in self.__taskHolders:
            if 'uiHintCloseAfterExecution' in taskHolder.tagNames():
                self.__closeAfterExecution = taskHolder.tag('uiHintCloseAfterExecution')

            if taskHolder.hasTag('uiHintShowInfoPanel'):
                self.__infoPanel.setVisible(taskHolder.tag('uiHintShowInfoPanel'))

            if 'uiHintTitle' in taskHolder.tagNames():
                self.__logo.setTextFormat(QtCore.Qt.RichText)
                self.__logo.setText("<b><big><big> {}".format(taskHolder.tag('uiHintTitle')))

            if 'uiHintDispatcher' in taskHolder.tagNames():
                self.__selectedDispatcher.selectDispatcher(taskHolder.tag('uiHintDispatcher'))

            if 'uiHintFilterDefaultTypes' in taskHolder.tagNames():
                filterDefaultTypes = taskHolder.tag('uiHintFilterDefaultTypes')

            if 'uiHintGlobRecursively' in taskHolder.tagNames():
                self.__uiHintGlobRecursively = taskHolder.tag('uiHintGlobRecursively')

            if taskHolder.tag('uiHintEmptyElementsMessage', None):
                self.__elementListWidget.setEmptyMessage(taskHolder.tag('uiHintEmptyElementsMessage'))

            if taskHolder.tag('uiHintBottomTaskHolderList', None):
                self.__splitter.setOrientation(QtCore.Qt.Vertical)
                self.__executionSettingsAreaWidget.setVisible(True)
                if 'uiHintBottomTaskHolderListEmptyMessage' in taskHolder.tagNames():
                    self.__executionSettingsEmptyMessageLabel.setText(taskHolder.tag('uiHintBottomTaskHolderListEmptyMessage'))
                self.refreshTaskHolderList()

            elif 'uiHintSkipSourceStep' in taskHolder.tagNames():
                skipSourceStep = taskHolder.tag('uiHintSkipSourceStep')

            if 'uiHintExecuteButtonLabel' in taskHolder.tagNames():
                self.__executeButton.setText(taskHolder.tag('uiHintExecuteButtonLabel'))
                if 'uiHintExecuteImmediately':
                    self.__nextButton.setText(self.__executeButton.text())
                    self.__nextButton.setIcon(QtGui.QIcon())

            # if there is a task holder that does not have any type specified to it, then we display all elements by
            # passing an empty list to the filter
            if len(taskHolder.matcher().matchTypes()) == 0:
                filterTypes = []
                break

            filterTypes += taskHolder.matcher().matchTypes()

        if filterTypes:
            filterTypes.extend(filterDefaultTypes)

        self.__nextButton.setVisible(self.__elementListWidget.checkableState() is not None)
        self.__selectedDispatcher.setVisible(self.__elementListWidget.checkableState() is not None)

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
            self.__elementListWidget.setElements(elementList)

        # forcing kombi to start at the execution settings (next) interface
        if skipSourceStep:
            self.refreshTaskHolderList()

    def __buildWidgets(self):
        """
        Create the widgets.
        """
        self.mainWidget().setLayout(QtWidgets.QVBoxLayout())
        self.__splitter = QtWidgets.QSplitter()

        sourceLayout = QtWidgets.QVBoxLayout()
        sourceLayout.setContentsMargins(0, 0, 0, 0)
        sourceControlMain = QtWidgets.QMainWindow()
        sourceBarLayout = QtWidgets.QHBoxLayout()

        self.__elementsLevelNavigationWidget = ElementLevelNavigationWidget()
        self.__sourceDirButton = QtWidgets.QPushButton()
        self.__sourceDirButton.setToolTip('Select a source directory')
        self.__sourceDirButton.setIcon(
            Resource.icon("icons/folder.png")
        )

        # refresh
        self.__sourceRefreshButton = QtWidgets.QPushButton()
        self.__sourceRefreshButton.setToolTip('Refresh the current listing')
        self.__sourceRefreshButton.setIcon(
            Resource.icon("icons/refresh.png")
        )

        # view options
        self.__moreButton = QtWidgets.QPushButton()
        self.__moreButton.setToolTip('Display more options')
        self.__moreButton.setIcon(
            Resource.icon("icons/more.png")
        )
        self.__moreButton.clicked.connect(self.__onShowMoreMenu)

        self.__sourceDirButton.clicked.connect(self.__onSelectSourceDir)
        self.__elementsLevelNavigationWidget.levelClicked.connect(self.setRootElement)
        self.__elementsLevelNavigationWidget.levelContextMenu.connect(self.__onContextMenu)
        sourceBarLayout.addWidget(self.__sourceDirButton)
        sourceBarLayout.addWidget(self.__elementsLevelNavigationWidget)
        sourceBarLayout.addWidget(self.__sourceRefreshButton)

        # info panel
        self.__infoPanel = QtWidgets.QDockWidget("Info")
        self.__infoPanel.setMinimumWidth(300)
        self.__infoPanel.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.__elementViewer = ElementViewerWidget([], centerAlignment=False)
        infoSplitter = QtWidgets.QSplitter()
        infoSplitter.setOrientation(QtCore.Qt.Vertical)
        infoSplitter.addWidget(self.__elementViewer)

        self.__detailsContainer = QtWidgets.QScrollArea()
        self.__detailsContainer.setWidgetResizable(True)
        self.__detailsContainer.setVisible(False)

        infoSplitter.addWidget(self.__detailsContainer)
        infoSplitter.setSizes([200, 400])
        self.__infoPanel.setWidget(infoSplitter)

        viewerButton = QtWidgets.QPushButton()
        viewerButton.setToolTip('Toggle the display of the info panel')
        viewerButton.setIcon(
            Resource.icon("icons/imageViewer.png")
        )

        sourceControlMain.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.__infoPanel)
        self.__infoPanel.setVisible(Resource.userConfig().value('showInfoPanel', True))
        sourceBarLayout.addWidget(viewerButton)

        viewerButton.clicked.connect(self.__onToggleInfoPanel)

        self.__scriptEditorButton = QtWidgets.QPushButton()
        self.__scriptEditorButton.setToolTip('Adds a new script editor tab')
        self.__scriptEditorButton.setIcon(
            Resource.icon("icons/python.png")
        )
        self.__scriptEditorButton.clicked.connect(lambda _: self.tabWidget().addScriptEditor())
        self.tabWidget().tabDisplayUpdate.connect(lambda x: self.__scriptEditorButton.setVisible(not x))
        sourceBarLayout.addWidget(self.__scriptEditorButton)
        self.__scriptEditorButton.setVisible(not self.tabWidget().hasScriptEditorTabs())

        sourceBarLayout.addWidget(self.__moreButton)
        sourceLayout.addLayout(sourceBarLayout)

        self.__sourceAreaWidget = QtWidgets.QWidget()
        self.__sourceAreaWidget.setLayout(sourceLayout)

        executionSettingsLayout = QtWidgets.QVBoxLayout()
        executionSettingsLayout.setContentsMargins(0, 0, 0, 0)

        self.__nextButton = QtWidgets.QPushButton("Next")
        self.__nextButton.setIcon(
            Resource.icon("icons/next.png")
        )
        self.__nextButton.clicked.connect(lambda _: self.refreshTaskHolderList())

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

        self.__elementListWidget = ElementListWidget()
        self.__elementListWidget.parentContextMenu.connect(self.__onContextMenu)
        self.__elementListWidget.itemSelectionChanged.connect(self.__onSourceTreeSelectionChanged)
        self.__elementListWidget.itemDoubleClicked.connect(self.__onSourceTreeDoubleClick)
        self.__elementListWidget.modifed.connect(self.__onForceRefresh)
        self.__sourceRefreshButton.clicked.connect(self.__onForceRefresh)

        self.__executionSettings = TaskHolderListWidget()
        sourceControlMain.setCentralWidget(self.__elementListWidget)

        sourceLayout.addWidget(sourceControlMain)
        executionSettingsLayout.addWidget(self.__executionSettings)
        self.__executionSettingsEmptyMessageLabel = QtWidgets.QLabel('', self.__executionSettings)
        self.__executionSettingsEmptyMessageLabel.move(10, 10)
        self.__executionSettingsEmptyMessageLabel.setVisible(False)

        # header
        headerLayout = QtWidgets.QHBoxLayout()
        self.mainWidget().layout().addLayout(headerLayout)

        self.__logo = QtWidgets.QLabel()
        if self.__customHeader:
            self.__logo.setTextFormat(QtCore.Qt.RichText)
            self.__logo.setText(self.__customHeader)
        elif len(self.__taskHolders):
            logoFilePath = "icons/header.png"
            if self.__taskHolders[0].tag('uiHintLogo', None):
                logoFilePath = self.__taskHolders[0].tag('uiHintLogo')
                if not os.path.isabs(logoFilePath):
                    logoFilePath = os.path.realpath(os.path.join(self.__taskHolders[0].var('configDirectory'), logoFilePath))

            self.__logo.setPixmap(Resource.pixmap(logoFilePath).scaledToHeight(48, QtCore.Qt.SmoothTransformation))
        self.__logo.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        headerLayout.addWidget(self.__logo)
        headerLayout.addStretch()

        self.mainWidget().layout().addWidget(self.__splitter)
        buttonLayout = QtWidgets.QHBoxLayout()
        self.mainWidget().layout().addLayout(buttonLayout)

        self.__executeButton = QtWidgets.QPushButton('Execute')
        self.__executeButton.setVisible(False)
        self.__executeButton.setToolTip('Performs the tasks')
        self.__executeButton.clicked.connect(self.__onPerformTasks)

        buttonLayout.addWidget(self.__selectedDispatcher)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.__backButton)
        buttonLayout.addWidget(self.__nextButton)
        buttonLayout.addWidget(self.__executeButton)

    def __onShowMoreMenu(self):
        """
        Display the more menu.
        """
        menu = QtWidgets.QMenu(self)

        preferencesAction = menu.addAction('Preferences')
        preferencesAction.triggered.connect(functools.partial(PreferencesWindow.popup, self))
        menu.addSeparator()

        # updating view mode
        listingModeMenu = menu.addMenu('Listing Mode')
        self.__viewModeActionGroup = QtWidgets.QActionGroup(self)
        for viewMode in self.__elementListWidget.viewModes:
            viewAction = listingModeMenu.addAction(viewMode.capitalize())
            viewAction.setCheckable(True)
            if viewMode == self.__elementListWidget.viewMode():
                viewAction.setChecked(True)
            viewAction.triggered.connect(functools.partial(self.__elementListWidget.setViewMode, viewMode))
            self.__viewModeActionGroup.addAction(viewAction)

        # vars
        showVarsAction = menu.addAction('Display Vars')
        showVarsAction.setCheckable(True)
        showVarsAction.setChecked(self.__elementListWidget.showVars())
        showVarsAction.triggered.connect(self.__onFilterShowVars)

        # tags
        showTagsAction = menu.addAction('Display Tags')
        showTagsAction.setCheckable(True)
        showTagsAction.setChecked(self.__elementListWidget.showTags())
        showTagsAction.triggered.connect(self.__onFilterShowTags)

        menu.exec_(QtGui.QCursor.pos())

    def __onForceRefresh(self):
        """
        Refresh the running window.
        """
        for rootElement in self.__rootElements:
            rootElement.flushChildrenCache()

        if self.__rootElements:
            self.setRootElement(self.__rootElements[-1])

        self.__elementListWidget.refresh()

    def __onPerformTasks(self):
        """
        Slog triggered by the run button.
        """
        selectedDispatcher = self.__selectedDispatcher.selectedDispatcher()
        dispatcher = Dispatcher.create(selectedDispatcher)

        if self.__executionSettings.execute(dispatcher, showOutput=False) and self.__closeAfterExecution:
            self.close()

    def __onContextMenu(self, element=None):
        """
        Slot triggered when there is a request for the context menu.

        In case the element is not specified we use the root current location.
        """
        menu = TasksMenu(self.__taskHolders, parent=self)
        menu.executed.connect(self.__onForceRefresh)
        menu.addElements([self.__rootElements[-1] if element is None else element])

        if len(menu.actions()):
            menu.exec_(QtGui.QCursor.pos())

    def __onSourceTreeSelectionChanged(self):
        """
        Slot called when selection changes on the element list.
        """
        elements = self.__elementListWidget.selectedElements()

        if self.__splitter.orientation() == QtCore.Qt.Vertical:
            self.refreshTaskHolderList(elements)

        if not (self.__infoPanel and self.__infoPanel.isVisible()):
            return

        self.__elementViewer.setElements(elements)
        self.__detailsContainer.setVisible(False)
        if not elements or 'details' not in elements[0].tagNames():
            return

        # computing details value
        value = getattr(elements[0], elements[0].tag('details'))()
        if value is None:
            return

        # in case of a non-QWidget result creating a widget based on OptionVisual
        if not isinstance(value, QtWidgets.QWidget):
            value = OptionVisual.create(value, {'readOnly': True, 'frame': False})

        self.__detailsContainer.setWidget(value)
        self.__detailsContainer.setVisible(True)

    def __onToggleInfoPanel(self):
        """
        Slot triggered when the info button is pressed.
        """
        self.__infoPanel.setVisible(not self.__infoPanel.isVisible())

        if self.__infoPanel.isVisible():
            self.__onSourceTreeSelectionChanged()

        if self.__infoPanel.isVisible() == Resource.userConfig().value('showInfoPanel', None):
            return

        Resource.userConfig().setValue('showInfoPanel', self.__infoPanel.isVisible())

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
        Slot triggered when an item is double clicked on the element list.
        """
        if isinstance(item, ElementsTreeWidgetItem) and not item.elements()[0].isLeaf():
            self.__rootElements.append(item.elements()[0])
            self.setRootElement(item.elements()[0])

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
            self.setRootElement(FsElement.createFromPath(selectedDirectory))

    def __onFilterShowVars(self, checked):
        """
        Slot triggered when info show vars is triggered.
        """
        self.__elementListWidget.setShowVars(checked)

    def __onFilterShowTags(self, checked):
        """
        Slot triggered when info show tags is triggered.
        """
        self.__elementListWidget.setShowTags(checked)

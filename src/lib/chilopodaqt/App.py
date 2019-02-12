import os
import re
import json
import datetime
import functools
import traceback
import platform
from collections import OrderedDict
from PySide2 import QtCore, QtGui, QtWidgets
from chilopoda.Dispatcher import Dispatcher
from chilopoda.ProcessExecution import ProcessExecution
from chilopoda.TaskHolderLoader import TaskHolderLoader
from chilopoda.Crawler import Crawler
from chilopoda.PathHolder import PathHolder
from .Resource import Resource
from .Style import Style

class App(QtWidgets.QApplication):
    """
    Basic graphical interface to pick files to run through a chilopoda configuration.

    Deprecation Notice: This interface is going to be phase out in future releases.

    Example:
        chilopoda <CONFIGURATION-DIRECTORY> [<INPUT-FILES-DIRECTORY>]
    """

    __viewModes = ["group", "flat"]
    __runOnTheFarm = os.environ.get('CHILOPODAAPP_RUN_FARM', '0')

    def __init__(self, argv, **kwargs):
        """
        Create a Chilopoda app.
        """
        super(App, self).__init__(argv, **kwargs)

        Style.apply(self)
        self.__configurationDirectory = ""
        self.__uiHintSourceColumns = []
        self.__buildWidgets()

        # getting configuration directory from the args
        if len(argv) > 1:
            self.__configurationDirectory = argv[1]

        # otherwise from the environment
        elif 'CHILOPODAAPP_CONFIG_DIR' in os.environ:
            self.__configurationDirectory = os.environ['CHILOPODAAPP_CONFIG_DIR']

        if self.updateConfiguration():
            self.__main.setWindowTitle('Chilopoda ({0})'.format(self.__configurationDirectory))

            # getting source files directory from the args
            if len(argv) > 2:
                self.__sourcePath.setText(':'.join(argv[2:]))

    def updateConfiguration(self):
        """
        Update the configuration used by chilopoda.
        """
        taskHolders = []
        currentVisibleCrawlers = self.__visibleCrawlers()

        # choosing a directory picker dialog
        if not self.__configurationDirectory:
            self.__configurationDirectory = self.__configurationDirectoryChooser()
            if not self.__configurationDirectory:
                return

        # collecting task holders from the directory
        taskHolderLoader = TaskHolderLoader()
        try:
            taskHolderLoader.loadFromDirectory(self.__configurationDirectory)
        except Exception as err:
            traceback.print_exc()

            QtWidgets.QMessageBox.critical(
               self.__main,
               "Chilopoda",
               "Failed to load the configuration ({0}):\n{1}".format(
                   self.__configurationDirectory,
                   str(err)
               ),
               QtWidgets.QMessageBox.Ok
            )

            raise err

        taskHolders = taskHolderLoader.taskHolders()
        if not taskHolders:
            result = QtWidgets.QMessageBox.warning(
                self.__main,
                "Chilopoda",
                "Selected directory does not contain any configuration for chilopoda!",
                QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok,
            )

            self.__configurationDirectory = ""

            # cancelled
            if result != QtWidgets.QMessageBox.Ok:
                self.__main.deleteLater()
                return False

        self.__updateSourceColumns(taskHolders)

        self.__taskHolders = taskHolders
        self.__onRefreshSourceDir()
        self.__processSourceTreeCrawlersVisibility(
            currentVisibleCrawlers
        )

        return True

    def updateSource(self, path):
        """
        Update the source tree.
        """
        self.__sourceTree.clear()
        self.__sourceViewCrawlerList = []
        self.__sourceFilterMenu.clear()
        self.__sourceOverrides = self.__loadSourceOverrides()

        if not path:
            return

        # we want to list in the interface only the crawler types used by the main tasks
        filterTypes = []
        for taskHolder in self.__taskHolders:
            matchTypes = taskHolder.crawlerMatcher().matchTypes()

            # if there is a task holder that does not have any type specified to it, then we display all crawlers by
            # passing an empty list to the filter
            if len(matchTypes) == 0:
                filterTypes = []
                break

            filterTypes += taskHolder.crawlerMatcher().matchTypes()

        # globbing crawlers
        crawlerList = []
        if os.path.exists(path):
            path = PathHolder(path)

        crawler = Crawler.create(path)
        globCrawlers = crawler.glob(filterTypes)

        # filtering the result of the glob, but now using the crawler matcher
        # this will match the variable types.
        for taskHolder in self.__taskHolders:
            for crawlerFound in globCrawlers:
                if crawlerFound in crawlerList:
                    continue

                if taskHolder.crawlerMatcher().match(crawlerFound):
                    crawlerList.append(crawlerFound)

        # sorting result by name
        crawlerList.sort(key=lambda x: x.var('name').lower())

        self.__updateSourceTreeCrawlerList(crawlerList, filterTypes)

    def updateTarget(self):
        """
        Update the target tree.
        """
        visibleCrawlers = self.__visibleCrawlers()

        # applying overrides
        self.__applySourceOverrides(
            self.__loadSourceOverrides(),
            visibleCrawlers
        )

        self.__targetAreaWidget.setVisible(True)
        self.__runOnTheFarmCheckbox.setVisible(True)
        self.__sourceAreaWidget.setVisible(False)

        self.__nextButton.setVisible(False)
        self.__backButton.setVisible(True)
        self.__runButton.setVisible(True)

        self.__targetTree.clear()

        for taskHolder in self.__taskHolders:
            try:
                matchedCrawlers = taskHolder.query(visibleCrawlers)
            except Exception as error:
                traceback.print_exc()

                QtWidgets.QMessageBox.critical(
                    self.__main,
                    "Template processing error",
                    "<nobr>" + str(error).replace("\n", "<br>") + "</nobr>",
                    QtWidgets.QMessageBox.Ok,
                )
                raise error

            groupedCrawlers = self.__groupCrawlers(matchedCrawlers.keys())

            if taskHolder.importTemplates():
                self.__createTask(self.__targetTree, taskHolder)
                continue

            for groupName, crawlerList in groupedCrawlers.items():
                for crawler in crawlerList:
                    nameSuffix = ""
                    if groupName is not None:
                        nameSuffix = " {} ({} total)".format(
                            matchedCrawlers[crawlerList[0]],
                            len(crawlerList)
                        )

                    matchedChild = self.__createTask(
                        self.__targetTree,
                        taskHolder,
                        nameSuffix
                    )

                    if groupName is not None:
                        filesEntry = QtWidgets.QTreeWidgetItem(matchedChild)
                        filesEntry.setData(0, QtCore.Qt.EditRole, 'Output')

                        for childCrawler in crawlerList:
                            child = QtWidgets.QTreeWidgetItem(filesEntry)
                            child.setData(1, QtCore.Qt.EditRole, matchedCrawlers[childCrawler])
                        break

        self.__targetTree.resizeColumnToContents(0)

    def __buildWidgets(self):
        """
        Create the widgets.
        """
        self.__main = QtWidgets.QMainWindow()
        self.__main.setWindowTitle('Chilopoda')
        self.__main.resize(1080, 720)
        self.__main.setWindowIcon(
            Resource.icon("icons/chilopoda.png")
        )

        centralWidget = QtWidgets.QWidget()
        self.__main.setCentralWidget(centralWidget)

        centralWidget.setLayout(QtWidgets.QVBoxLayout())
        treeArea = QtWidgets.QSplitter()

        sourceLayout = QtWidgets.QVBoxLayout()
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
        self.__sourceRefreshButton.setVisible(False)
        self.__sourceRefreshButton.setIcon(
            self.__sourceRefreshButton.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload)
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
        self.__sourceFilterButton = QtWidgets.QPushButton("Filter View")
        self.__sourceFilterButton.setToolTip('Filters out specific crawler types')
        self.__sourceFilterButton.setIcon(
            Resource.icon("icons/filterView.png")
        )
        self.__sourceFilterMenu = QtWidgets.QMenu(self.__sourceFilterButton)
        self.__sourceFilterButton.setMenu(self.__sourceFilterMenu)

        self.__sourceDirButton.clicked.connect(self.__onSelectSourceDir)
        self.__sourceRefreshButton.clicked.connect(self.__onRefreshSourceDir)
        self.__sourcePath.textChanged.connect(self.updateSource)

        sourceBarLayout.addWidget(self.__sourceDirButton)
        sourceBarLayout.addWidget(self.__sourcePath)
        sourceBarLayout.addWidget(self.__sourceRefreshButton)
        sourceBarLayout.addWidget(self.__sourceViewModeButton)
        sourceBarLayout.addWidget(self.__sourceFilterButton)

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
        self.__runOnTheFarmCheckbox = QtWidgets.QCheckBox("Run on the farm")
        if self.__runOnTheFarm and self.__runOnTheFarm.lower() in ["true", "1"]:
            self.__runOnTheFarmCheckbox.setChecked(True)
        self.__runOnTheFarmCheckbox.setVisible(False)

        targetBarLayout = QtWidgets.QHBoxLayout()
        targetLayout.addLayout(targetBarLayout)

        treeArea.addWidget(self.__sourceAreaWidget)
        treeArea.addWidget(self.__targetAreaWidget)

        self.__sourceTree = self.__treeWidget(["Source"])
        self.__sourceTree.itemChanged.connect(self.__onSourceTreeItemCheckedChanged)
        self.__sourceTree.customContextMenuRequested.connect(self.__onSourceTreeContextMenu)

        self.__targetTree = self.__treeWidget(["Target"])
        self.__targetTree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.__targetTree.customContextMenuRequested.connect(self.__onTargetTreeContextMenu)

        sourceLayout.addWidget(self.__sourceTree)
        targetLayout.addWidget(self.__targetTree)

        # header
        headerLayout = QtWidgets.QHBoxLayout()
        centralWidget.layout().addLayout(headerLayout)

        logo = QtWidgets.QLabel()

        logo.setPixmap(Resource.pixmap("icons/header.png").scaledToHeight(64, QtCore.Qt.SmoothTransformation))
        logo.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        headerLayout.addWidget(
            logo
        )

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

        buttonLayout.addWidget(self.__runOnTheFarmCheckbox)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.__backButton)
        buttonLayout.addWidget(self.__nextButton)
        buttonLayout.addWidget(self.__runButton)

        self.__main.show()

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

    @classmethod
    def __camelCaseToSpaced(cls, text):
        return text[0].upper() + re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>", text[1:])

    def __updateSourceColumns(self, taskHolders):
        """
        Update the source columns.
        """
        # updating columns
        columns = []
        for taskHolder in filter(lambda x: '__uiHintSourceColumns' in x.varNames(), taskHolders):
            for columnName in filter(lambda x: x not in columns, taskHolder.var('__uiHintSourceColumns')):
                columns.append(columnName)

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

    def __configurationDirectoryChooser(self):
        """
        Display the chooser dialog to select a directory containing configurations.
        """
        configurationDirectory = ""

        while not configurationDirectory:
            if configurationDirectory == "":
                configurationDirectory = QtWidgets.QFileDialog.getExistingDirectory(
                    self.__main,
                    "Select a directory with the configuration that should be used by chilopoda",
                    configurationDirectory,
                    QtWidgets.QFileDialog.ShowDirsOnly
                )

                # cancelled
                if configurationDirectory == "":
                    self.__main.deleteLater()
                    break

        return configurationDirectory

    def __processSourceTreeCrawlersVisibility(self, currentVisibleCrawlers):
        """
        Process the visibility of source tree crawlers.
        """
        # visible crawlers
        totalRows = self.__sourceTree.model().rowCount()
        for i in range(totalRows):
            crawler = self.__sourceViewCrawlerList[i]

            if not self.__sourceTree.isRowHidden(i, QtCore.QModelIndex()):
                visible = False
                for visibleCrawler in currentVisibleCrawlers:
                    if isinstance(visibleCrawler, list):
                        useVisibleCrawler = visibleCrawler[0]
                    else:
                        useVisibleCrawler = visibleCrawler

                    if isinstance(crawler, list):
                        useCrawler = crawler[0]
                    else:
                        useCrawler = crawler

                    if useVisibleCrawler.var('fullPath') == useCrawler.var('fullPath'):
                        visible = True
                        break

                item = self.__sourceTree.topLevelItem(i)

                if not visible:
                    item.setCheckState(0, QtCore.Qt.Unchecked)

    def __updateSourceTreeCrawlerList(self, crawlerList, filterTypes):
        """
        Update the crawlers displayed in the source tree.
        """
        crawlerTypes = set()
        crawlerTags = {}

        # group
        if self.__checkedViewMode == "Group":
            groupedCrawlers = self.__groupCrawlers(crawlerList)

            for groupName in groupedCrawlers.keys():
                if groupName:
                    parent = QtWidgets.QTreeWidgetItem(self.__sourceTree)

                    # visible data
                    visibleGroupName = groupName + '   '
                    if visibleGroupName.startswith(os.sep):
                        visibleGroupName = visibleGroupName[1:]

                    parent.setData(0, QtCore.Qt.EditRole, visibleGroupName)

                    # adding column information
                    self.__addSourceTreeColumnData(groupedCrawlers[groupName][0], parent)

                    parent.setFlags(parent.flags() | QtCore.Qt.ItemIsUserCheckable)
                    parent.setCheckState(0, QtCore.Qt.Checked)

                    self.__sourceViewCrawlerList.append(groupedCrawlers[groupName])
                    for crawler in groupedCrawlers[groupName]:
                        self.__createSourceTreeChildItem(
                            crawler,
                            parent,
                            crawlerTypes,
                            crawlerTags
                        )

                else:
                    for crawler in groupedCrawlers[groupName]:
                        self.__sourceViewCrawlerList.append(crawler)
                        child = self.__createSourceTreeChildItem(
                            crawler,
                            self.__sourceTree,
                            crawlerTypes,
                            crawlerTags
                        )

                        child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                        child.setCheckState(0, QtCore.Qt.Checked)

                        self.__addSourceTreeColumnData(crawler, child)

        # flat
        else:
            for crawler in sorted(crawlerList, key=lambda x: x.var('fullPath')):

                # only testing with the first crawler when grouped
                if isinstance(crawler, list):
                    crawler = crawler[0]

                self.__sourceViewCrawlerList.append(crawler)
                child = self.__createSourceTreeChildItem(crawler, self.__sourceTree, crawlerTypes, crawlerTags)
                child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                child.setCheckState(0, QtCore.Qt.Checked)
                self.__addSourceTreeColumnData(crawler, child)

        # crawler types
        self.__crawlerTypesMenu = self.__sourceFilterMenu.addMenu('Types')

        allAction = self.__crawlerTypesMenu.addAction('ALL')
        allAction.triggered.connect(self.__onFilterSelectAll)

        noneAction = self.__crawlerTypesMenu.addAction('NONE')
        noneAction.triggered.connect(self.__onFilterSelectNone)
        self.__crawlerTypesMenu.addSeparator()

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

    def __launchDefaultApp(self, filePath):
        """
        Open the input file path in the default app.
        """
        args = []
        filePath = os.path.normpath(filePath)

        # linux
        if platform.system() == 'Linux':
            args = ('xdg-open', filePath)
        # windows
        elif platform.system() == 'Windows':
            args = ('cmd', '/C', 'start', '""', filePath.replace("\\", "\\\\"))
        # macos
        elif platform.system() == 'Darwin':
            args = ('open', filePath)

        assert args

        processExecution = ProcessExecution(
            args,
            shell=True,
            redirectStderrToStdout=True
        )

        processExecution.execute()

    def __treeWidget(self, columns=[]):
        """
        Return a tree widget used by source and target.
        """
        sourceTree = QtWidgets.QTreeWidget()

        sourceTree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        sourceTree.setSelectionBehavior(QtWidgets.QTreeWidget.SelectItems)
        sourceTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        header = QtWidgets.QTreeWidgetItem(columns)
        sourceTree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        sourceTree.setHeaderItem(header)

        return sourceTree

    def __visibleCrawlers(self):
        """
        Return a list of visible crawlers in the source tree.
        """
        totalRows = self.__sourceTree.model().rowCount()
        result = []
        for i in range(totalRows):
            self.__sourceTree.model().index(i, 0)
            if not self.__sourceTree.isRowHidden(i, QtCore.QModelIndex()):
                item = self.__sourceTree.topLevelItem(i)
                if item.checkState(0):

                    crawler = self.__sourceViewCrawlerList[i]
                    if isinstance(crawler, list):
                        result += crawler
                    else:
                        result.append(crawler)

        return list(map(lambda x: x.clone(), result))

    def __createSubtasks(self, parentEntry, taskHolder):
        """
        Create the sub tasks widget information.
        """
        if taskHolder.subTaskHolders():
            subTaskChild = QtWidgets.QTreeWidgetItem(parentEntry)
            subTaskChild.setData(0, QtCore.Qt.EditRole, 'Sub tasks')
            subTaskChild.setExpanded(True)

            for childTaskHolder in taskHolder.subTaskHolders():
                self.__createTask(subTaskChild, childTaskHolder)

    def __createTask(self, parentEntry, taskHolder, suffix=''):
        """
        Create the task widget information.
        """
        taskName = taskHolder.task().type()

        taskChild = QtWidgets.QTreeWidgetItem(parentEntry)
        taskChild.setData(0, QtCore.Qt.EditRole, self.__camelCaseToSpaced(taskName))
        taskChild.setData(1, QtCore.Qt.EditRole, suffix)
        taskChild.setExpanded(True)

        # options
        optionsEntry = QtWidgets.QTreeWidgetItem(taskChild)
        optionsEntry.setData(0, QtCore.Qt.EditRole, 'Options')
        optionsEntry.setExpanded(True)
        for optionName in taskHolder.task().optionNames():
            optionEntry = QtWidgets.QTreeWidgetItem(optionsEntry)
            optionEntry.setData(0, QtCore.Qt.EditRole, self.__camelCaseToSpaced(optionName))

            w = None
            signal = None
            value = taskHolder.task().option(optionName)
            if isinstance(value, bool):
                w = QtWidgets.QCheckBox()
                w.setChecked(value)
                signal = w.stateChanged

            elif isinstance(value, (list, tuple)):
                w = QtWidgets.QComboBox()
                w.setMaximumWidth(300)
                w.addItems(value)
                signal = w.activated

            elif isinstance(value, int):
                w = QtWidgets.QSpinBox()
                w.setMaximumWidth(150)
                w.setRange(-99999999, 99999999)
                w.setValue(value)
                signal = w.editingFinished

            elif isinstance(value, float):
                w = QtWidgets.QDoubleSpinBox()
                w.setMaximumWidth(150)
                w.setRange(-99999999, 99999999)
                w.setValue(value)
                signal = w.editingFinished

            else:
                w = QtWidgets.QLineEdit(str(value))
                signal = w.editingFinished

            signal.connect(functools.partial(self.__editOption, w, optionName, taskHolder))

            self.__targetTree.setItemWidget(optionEntry, 1, w)
            self.__targetTree.openPersistentEditor(optionEntry, 1)

        # advanced
        advancedEntry = QtWidgets.QTreeWidgetItem(optionsEntry)
        advancedEntry.setData(0, QtCore.Qt.EditRole, 'Advanced')

        if 'contextConfig' in taskHolder.varNames():
            configName = QtWidgets.QTreeWidgetItem(advancedEntry)
            configName.setData(0, QtCore.Qt.EditRole, "Config")
            configName.setData(1, QtCore.Qt.EditRole, taskHolder.var('contextConfig'))

        # target template
        templateEntry = QtWidgets.QTreeWidgetItem(advancedEntry)
        templateEntry.setData(0, QtCore.Qt.EditRole, 'Target')
        templateWidget = QtWidgets.QLineEdit(taskHolder.targetTemplate().inputString())
        self.__targetTree.setItemWidget(
            templateEntry,
            1,
            templateWidget
        )
        templateWidget.editingFinished.connect(functools.partial(self.__editTemplate, templateWidget, "target", taskHolder))

        # filter template
        filterTemplate = QtWidgets.QTreeWidgetItem(advancedEntry)
        filterTemplate.setData(0, QtCore.Qt.EditRole, 'Filter')
        templateWidget = QtWidgets.QLineEdit(taskHolder.filterTemplate().inputString())
        self.__targetTree.setItemWidget(
            filterTemplate,
            1,
            templateWidget
        )
        templateWidget.editingFinished.connect(functools.partial(self.__editTemplate, templateWidget, "filter", taskHolder))

        # export
        exportEntry = QtWidgets.QTreeWidgetItem(advancedEntry)
        exportEntry.setData(0, QtCore.Qt.EditRole, 'Export')
        templateWidget = QtWidgets.QLineEdit(taskHolder.exportTemplate().inputString())
        self.__targetTree.setItemWidget(
            exportEntry,
            1,
            templateWidget
        )
        templateWidget.editingFinished.connect(functools.partial(self.__editTemplate, templateWidget, "export", taskHolder))

        # imports
        if taskHolder.importTemplates():
            importsChild = QtWidgets.QTreeWidgetItem(advancedEntry)
            importsChild.setData(0, QtCore.Qt.EditRole, 'Imports')

            for importTemplate in taskHolder.importTemplates():
                child = QtWidgets.QTreeWidgetItem(importsChild)
                child.setData(1, QtCore.Qt.EditRole, importTemplate.inputString())

        self.__createSubtasks(taskChild, taskHolder)

        return taskChild

    def __editOption(self, widget, optionName, taskHolder, value=None):
        """
        Edit a task holder option.
        """
        if isinstance(widget, QtWidgets.QCheckBox):
            taskHolder.task().setOption(optionName, widget.isChecked())

        elif isinstance(widget, QtWidgets.QLineEdit):
            taskHolder.task().setOption(optionName, widget.text())

        elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
            taskHolder.task().setOption(optionName, widget.value())

    def __editTemplate(self, widget, template, taskHolder, value=None):
        """
        Edit a template.
        """
        value = widget.text()
        if template == "target":
            taskHolder.targetTemplate().setInputString(value)

        elif template == "filter":
            taskHolder.filterTemplate().setInputString(value)

        elif template == "export":
            taskHolder.exportTemplate().setInputString(value)

    def __sourceOverridesConfig(self):
        """
        Return the full path about the location for the override files.
        """
        return os.path.join(self.__configurationDirectory, "overrides", "source.json")

    def __loadSourceOverrides(self):
        """
        Load crawler overrides in the source tree.
        """
        result = {}

        if os.path.exists(self.__sourceOverridesConfig()):
            with open(self.__sourceOverridesConfig()) as sourceFile:
                result = json.load(sourceFile)

        return result

    def __applySourceOverrides(self, overrides, crawlers):
        """
        Apply overrides overrides on the source tree.
        """
        if not overrides:
            return

        for crawler in crawlers:
            fullPath = crawler.var('fullPath')
            if fullPath in overrides:
                for varName, varValue in overrides[fullPath].items():
                    crawler.setVar(varName, varValue)

    def __addSourceTreeColumnData(self, crawler, treeItem):
        """
        Add crawler information to a column in the source tree.
        """
        # adding column information
        for index, column in enumerate(self.__uiHintSourceColumns):

            hasOverride = False
            value = ''
            if crawler.var('fullPath') in self.__sourceOverrides and column in self.__sourceOverrides[crawler.var('fullPath')]:
                value = self.__sourceOverrides[crawler.var('fullPath')][column]
                hasOverride = True

            if column in crawler.varNames():
                if not hasOverride:
                    value = crawler.var(column)

            treeItem.setData(
                index + 1,
                QtCore.Qt.EditRole,
                str(value) + '   '
            )

            if hasOverride:
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

        # visible data
        child.setData(0, QtCore.Qt.EditRole, crawler.var('baseName') + '   ')
        self.__addSourceTreeColumnData(crawler, child)

        crawlerTypes.add(crawler.var('type'))

        # adding tags
        for tagName in crawler.tagNames():
            if tagName not in crawlerTags:
                crawlerTags[tagName] = set()
            crawlerTags[tagName].add(crawler.tag(tagName))

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

        tags = QtWidgets.QTreeWidgetItem(child)
        tags.setData(
            0,
            QtCore.Qt.EditRole,
            'tags'
        )

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
        self.__runOnTheFarmCheckbox.setVisible(False)
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
        if not self.__targetTree.model().rowCount():
            QtWidgets.QMessageBox.information(
                self.__main,
                "Chilopoda",
                "No targets available (refresh the targets)!",
                QtWidgets.QMessageBox.Ok
            )
            return

        visibleCrawlers = self.__visibleCrawlers()

        # applying overrides
        self.__applySourceOverrides(
            self.__loadSourceOverrides(),
            visibleCrawlers
        )

        groupedVisibleCrawlers = Crawler.group(visibleCrawlers)
        output = []
        try:
            for crawlersGroup in groupedVisibleCrawlers:
                for taskHolder in self.__taskHolders:

                    # run on the farm
                    if self.__runOnTheFarmCheckbox.checkState() == QtCore.Qt.Checked:
                        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        renderFarmDispatcher = Dispatcher.create('renderFarm')
                        label = os.path.basename(taskHolder.var('configDirectory'))
                        label += "/"
                        label += os.path.splitext(taskHolder.var('configName'))[0]
                        label += date
                        label += ": "
                        label += crawlersGroup[0].tag('group') if 'group' in crawlersGroup[0].tagNames() else crawlersGroup[0].var('baseName')
                        renderFarmDispatcher.setOption('label', label)
                        renderFarmDispatcher.dispatch(taskHolder, crawlersGroup)

                    # run locally
                    else:
                        localDispatcher = Dispatcher.create('local')
                        localDispatcher.setOption('awaitExecution', True)
                        for processExecution in localDispatcher.dispatch(taskHolder, crawlersGroup):
                            output += processExecution.stdout()

        except Exception as err:
            traceback.print_exc()

            messageBox = QtWidgets.QMessageBox(
               self.__main,
               "Chilopoda",
               QtWidgets.QMessageBox.Ok
            )
            messageBox.setIcon(QtWidgets.QMessageBox.Critical)
            messageBox.setText("Failed during execution")
            messageBox.setDetailedText(str(err))
            messageBox.show()

            raise err

        else:
            message = "Execution completed!"
            if self.__runOnTheFarmCheckbox.checkState() == QtCore.Qt.Checked:
                message = "Execution submitted to the farm!"

            QtWidgets.QMessageBox.information(
                self.__main,
                "Chilopoda",
                message,
                QtWidgets.QMessageBox.Ok
            )

            # showing the output for local executions
            if not self.__runOnTheFarmCheckbox.checkState() == QtCore.Qt.Checked:
                self.__outputWidget = QtWidgets.QPlainTextEdit()
                self.__outputWidget.setPlainText(''.join(output))
                self.__outputWidget.setWindowTitle('Output')
                self.__outputWidget.setMinimumWidth(920)
                self.__outputWidget.setMinimumHeight(600)
                self.__outputWidget.setVisible(True)

    def __onSourceTreeContextMenu(self, point):
        """
        Slot triggered when context menu from source tree is triggered.
        """
        self.__sourceTree.resizeColumnToContents(0)

        selectedIndexes = self.__sourceTree.selectionModel().selectedIndexes()

        if selectedIndexes:
            selectedColumn = selectedIndexes[0].column()
            menu = QtWidgets.QMenu(self.__main)
            if selectedColumn == 0:
                action = menu.addAction('Show Folder')
                action.triggered.connect(self.__onShowFolder)

                action = menu.addAction('Open')
                action.triggered.connect(self.__onOpenSelected)
            else:
                action = menu.addAction('Override Value')
                action.triggered.connect(self.__onChangeCrawlerValue)

                action = menu.addAction('Reset Value')
                action.triggered.connect(self.__onResetCrawlerValue)

            menu.exec_(self.__sourceTree.mapToGlobal(point))

    def __onChangeCrawlerValue(self):
        """
        Slot triggered when an override in the source tree is triggered.
        """
        value = None
        overrides = dict(self.__sourceOverrides)
        for selectedIndex in filter(lambda x: x.parent().row() == -1, self.__sourceTree.selectionModel().selectedIndexes()):
            selectedColumn = selectedIndex.column()
            columnName = self.__uiHintSourceColumns[selectedColumn - 1]

            crawler = self.__sourceViewCrawlerList[selectedIndex.row()]
            if not isinstance(crawler, list):
                crawler = [crawler]

            hintValue = ""
            if columnName in crawler[0].varNames():
                hintValue = crawler[0].var(columnName)

            if value is None:
                value = QtWidgets.QInputDialog.getText(
                    self.__main,
                    "Override Value",
                    "New Value",
                    QtWidgets.QLineEdit.Normal,
                    str(hintValue)
                )

                # cancelled
                if not value[1]:
                    return

                value = type(hintValue)(value[0])

            for crawlerItem in crawler:
                if crawlerItem.var('fullPath') not in overrides:
                    overrides[crawlerItem.var('fullPath')] = {}

                overrides[crawlerItem.var('fullPath')][columnName] = value

        if not os.path.exists(os.path.dirname(self.__sourceOverridesConfig())):
            os.mkdir(os.path.dirname(self.__sourceOverridesConfig()))

        with open(self.__sourceOverridesConfig(), 'w') as sourceFile:
            json.dump(overrides, sourceFile, indent=4)

        if value is not None:
            self.__onRefreshSourceDir()

    def __onResetCrawlerValue(self):
        """
        Slot triggered when an override in the source tree is removed.
        """
        overrides = dict(self.__sourceOverrides)
        for selectedIndex in self.__sourceTree.selectionModel().selectedIndexes():
            selectedColumn = selectedIndex.column()

            if selectedIndex.parent().row() != -1:
                continue

            columnName = self.__uiHintSourceColumns[selectedColumn - 1]

            crawler = self.__sourceViewCrawlerList[selectedIndex.row()]
            if not isinstance(crawler, list):
                crawler = [crawler]

            crawlerFilePaths = map(lambda x: x.var('fullPath'), crawler)
            for fullPath in crawlerFilePaths:
                if fullPath in overrides:
                    if columnName in overrides[fullPath]:
                        del overrides[fullPath][columnName]

                    if not len(overrides[fullPath]):
                        del overrides[fullPath]

        if os.path.exists(os.path.dirname(self.__sourceOverridesConfig())):
            with open(self.__sourceOverridesConfig(), 'w') as sourceFile:
                json.dump(overrides, sourceFile, indent=4)

            self.__onRefreshSourceDir()

    def __onTargetTreeContextMenu(self, point):
        """
        Slot triggered when the context menu in the target tree is triggered.
        """
        selectedIndexes = self.__targetTree.selectionModel().selectedIndexes()
        if selectedIndexes:
            value = selectedIndexes[0].data(0)

            if os.path.splitext(str(value))[-1][1:] in TaskHolderLoader.registeredNames():
                menu = QtWidgets.QMenu(self.__main)
                action = menu.addAction('Show Config')
                action.triggered.connect(functools.partial(self.__launchDefaultApp, value))

                menu.exec_(self.__sourceTree.mapToGlobal(point))

    def __onShowFolder(self):
        """
        Slot triggered when show folder for the selected crawlers is triggered.
        """
        folderPaths = set()
        for index, crawler in enumerate(self.__sourceViewCrawlerList):

            if isinstance(crawler, list):
                crawler = crawler[0]

            item = self.__sourceTree.topLevelItem(index)
            if item.isSelected():
                folderPaths.add(os.path.dirname(crawler.var('fullPath')))

        for folderPath in folderPaths:
            self.__launchDefaultApp(
                folderPath
            )

    def __onOpenSelected(self):
        """
        Slot triggered when open the select file is triggered.
        """
        for index, crawler in enumerate(self.__sourceViewCrawlerList):

            if isinstance(crawler, list):
                crawler = crawler[0]

            item = self.__sourceTree.topLevelItem(index)
            if item.isSelected():
                self.__launchDefaultApp(crawler.var('fullPath'))

    def __onSelectSourceDir(self):
        """
        Slot triggered when select source button is triggered.
        """
        currentDir = self.__sourcePath.text() or '/'
        selectedDirectory = QtWidgets.QFileDialog.getExistingDirectory(
            self.__main,
            "Select source directory",
            currentDir,
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if selectedDirectory not in ['', '/']:
            self.__sourcePath.setText(selectedDirectory)

    def __onRefreshSourceDir(self):
        """
        Slot triggered when refresh button from source tree is triggered.
        """
        self.updateSource(self.__sourcePath.text())

    def __onFilterSelectNone(self):
        """
        Slot triggered when select none filter is triggered.
        """
        self.__onFilterSelectAll(False)

    def __onFilterSelectAll(self, checked=True):
        """
        Slot triggered when select all filter is triggered.
        """
        for action in self.__crawlerTypesMenu.actions():
            action.setChecked(checked)

    def __onSourceFiltersChanged(self):
        """
        Slot triggered a filter is changed in the source tree.
        """
        visibleTypes = []
        for action in self.__crawlerTypesMenu.actions():
            if action.isChecked():
                visibleTypes.append(action.text())

        totalRows = self.__sourceTree.model().rowCount()
        for i in range(totalRows):
            crawler = self.__sourceViewCrawlerList[i]

            # only testing with the first crawler when grouped
            if isinstance(crawler, list):
                crawler = crawler[0]

            self.__sourceTree.model().index(i, 0)

            self.__sourceTree.setRowHidden(
                i,
                QtCore.QModelIndex(),
                (crawler.var('type') not in visibleTypes)
            )

    def __onSourceTreeItemCheckedChanged(self, currentItem):
        """
        Slot triggered when the check state of an item in the source tree is changed.
        """
        if not currentItem.isSelected() or not self.__sourceTree.selectionModel().selectedIndexes():
            return

        for index in range(len(self.__sourceViewCrawlerList)):
            item = self.__sourceTree.topLevelItem(index)
            if item.isSelected():
                item.setCheckState(0, currentItem.checkState(0))

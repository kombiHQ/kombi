import pathlib
import difflib
import functools
from Qt import QtWidgets, QtCore, QtGui
from kombi.Config import Config
from kombi.Task import Task
from kombi.Element.Fs.FsElement import FsElement
from ..Resource import Resource
from ..Widget.ScriptEditorWidget import ScriptEditorWidget

class ScriptEditorTabWidget(QtWidgets.QTabWidget):
    """
    This class represents a tab widget for managing script editor tabs.

    It allows adding script editor tabs, renaming tabs, closing tabs,
    and saving/restoring tab states via user configuration.
    """
    tabDisplayUpdate = QtCore.Signal(bool)
    __scriptEditorsConfig = Config('scriptEditors')
    __showTabIcon = False

    def __init__(self, mainWidget=None, loadUserTabs=True, parent=None):
        """
        Create ScriptEditorWidget object.
        """
        super().__init__(parent=parent)
        self.setTabBar(_ScriptEditorTabBarWidget())
        self.setTabsClosable(True)
        self.setMovable(False)

        if mainWidget:
            self.__setMainWidget(mainWidget)

        if loadUserTabs:
            self.__loadUserTabs()

            # after loading the tabs, we need to update their indices
            # to ensure they are aligned with the current active tab index.
            self.__bakeTabs()

        if not self.count():
            self.addScriptEditor()

        self.tabCloseRequested.connect(self.__onTabClose)
        self.tabBar().tabRenamed.connect(self.__onCodeChanged)
        self.tabBar().tabMoved.connect(self.__onTabMoved)
        self.tabBar().currentChanged.connect(self.__onTabChanged)

        scriptEditorButton = QtWidgets.QPushButton()
        scriptEditorButton.setToolTip('Adds a new script editor tab')
        scriptEditorButton.setIcon(
            Resource.icon("icons/python.png")
        )
        scriptEditorButton.clicked.connect(lambda _: self.addScriptEditor())

        buttonsWidget = QtWidgets.QWidget()
        self.__cornerButtonsLayout = QtWidgets.QHBoxLayout()
        self.__cornerButtonsLayout.setContentsMargins(10, 0, 10, 0)
        buttonsWidget.setLayout(self.__cornerButtonsLayout)
        self.appendCornerButtonWidget(scriptEditorButton)

        self.setCornerWidget(buttonsWidget, corner=QtCore.Qt.TopRightCorner)

        self.displayUpdate()

    def appendCornerButtonWidget(self, widget):
        """
        Append a custom widget to the right corner panel.
        """
        assert isinstance(widget, QtWidgets.QWidget), 'Invalid widget type!'

        self.__cornerButtonsLayout.addWidget(widget)

    def printHelp(self, additionalHelp=None):
        """
        Print the formatted help in the output widget.

        The additionalHelp argument allows you to pass a list of extra lines
        that will be included as part of the help content.
        """
        if not self.isTabScriptEditor(self.currentIndex()):
            return

        scriptEditor = self.widget(self.currentIndex())
        scriptEditor.printHelp(additionalHelp)

    def mainWidget(self):
        """
        Return the main widget associated with the script editor tab widget or None.
        """
        return self.__mainWidget

    def addScriptEditor(self, code='', filePath='', tabName='Script Editor', setFocus=True):
        """
        Add a new script editor tab to the widget.
        """
        # in case the input file path is already loaded. Don't create a new tab.
        if filePath:
            for i in range(self.tabBar().count()):
                widget = self.widget(i)
                if isinstance(widget, ScriptEditorWidget) and widget.filePath() == filePath:
                    tabIndex = i
                    if setFocus:
                        self.setCurrentIndex(tabIndex)
                    return tabIndex

        scriptEditor = ScriptEditorWidget(code, filePath)
        tabIndex = self.addTab(scriptEditor, tabName)
        if self.__showTabIcon:
            icon = Resource.icon("icons/python.png")
            if filePath:
                icon = QtWidgets.QFileIconProvider().icon(QtCore.QFileInfo(filePath))
            self.setTabIcon(tabIndex, icon)

        self.displayUpdate()
        self.__updateTabStatus(tabIndex)
        scriptEditor.codeChanged.connect(functools.partial(self.__onCodeChanged, tabIndex))
        scriptEditor.openFilePath.connect(self.__onScriptEditorOpenFilePAth)

        if setFocus:
            self.setCurrentIndex(tabIndex)

        return tabIndex

    def hasScriptEditorTabs(self):
        """
        Return a boolean telling if there are script editor tabs.
        """
        for i in range(self.tabBar().count()):
            if isinstance(self.widget(i), ScriptEditorWidget):
                return True
        return False

    def displayUpdate(self):
        """
        Update the visibility of the tab bar based on the number of tabs.
        """
        showTabs = self.hasScriptEditorTabs()
        if showTabs:
            self.tabBar().show()
        else:
            self.tabBar().hide()

        self.tabDisplayUpdate.emit(showTabs)

    def isTabScriptEditor(self, tabIndex):
        """
        Return a boolean if tab contains a script editor.
        """
        widget = self.widget(tabIndex)
        return isinstance(widget, ScriptEditorWidget)

    def __onScriptEditorOpenFilePAth(self, filePath, line=0):
        """
        Triggered when openfilePath signal is emitted by the script editor widget.
        """
        tabIndex = self.addScriptEditor(filePath=filePath)
        self.widget(tabIndex).gotoLine(line)

    def __setMainWidget(self, mainWidget):
        """
        Set the main widget tab that will not be closable.
        """
        self.__mainWidget = mainWidget

        self.addTab(mainWidget, 'Main')
        self.tabBar().removeCloseButton(0)

    def __bakeTabs(self):
        """
        Serialize all script editor tabs.
        """
        # removing all tabs
        for keyName in list(self.__scriptEditorsConfig.keys()):
            if keyName.isdigit():
                self.__scriptEditorsConfig.removeKey(keyName)

        # serializing active tabs
        for tabIndex in range(self.tabBar().count()):
            if not isinstance(self.widget(tabIndex), ScriptEditorWidget):
                continue
            self.__onCodeChanged(tabIndex, serialize=False)

        self.__scriptEditorsConfig.serialize()
        self.displayUpdate()

    def __loadUserTabs(self):
        """
        Load previously saved script editor tabs from the user configuration.
        """
        for keyName in sorted(filter(lambda x: x.isdigit(), self.__scriptEditorsConfig.keys()), key=lambda x: int(x)):
            tabInfo = self.__scriptEditorsConfig.value(keyName)
            self.addScriptEditor(
                tabInfo['code'],
                tabInfo['filePath'],
                tabInfo['label'],
                setFocus=False
            )

    def __onTabClose(self, index):
        """
        Triggered when tab close button is pressed.
        """
        # prompting for confirmation to prevent potential data loss
        if self.isTabScriptEditor(index):
            tabWidget = self.widget(index)
            if tabWidget.filePath() and tabWidget.isModified() or \
                    len(tabWidget.code()) and not tabWidget.filePath():
                closeConfirmation = QtWidgets.QMessageBox.question(
                    self,
                    'Close Tab: {}'.format(self.tabText(index)),
                    'Are you sure you want to close? Unsaved changes will be lost.',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                if closeConfirmation != QtWidgets.QMessageBox.Yes:
                    return

        self.removeTab(index)
        self.__bakeTabs()

        if not self.count():
            self.addScriptEditor()

    def __onTabChanged(self, tabIndex):
        """
        Triggered when tab index changed.
        """
        widget = self.widget(tabIndex)
        if isinstance(widget, ScriptEditorWidget):
            widget.codeEditorWidget().setFocus()

    def __onTabMoved(self, *_):
        """
        Triggered when a tab is moved.
        """
        self.__bakeTabs()

    def __onCodeChanged(self, tabIndex, serialize=True):
        """
        Triggered when code inside a script editor tab has changed.
        """
        scriptEditor = self.widget(tabIndex)
        if scriptEditor is None:
            return

        tabName = self.tabText(tabIndex)
        self.__updateTabStatus(tabIndex)

        self.__scriptEditorsConfig.setValue(
            str(tabIndex),
            {
                'label': tabName,
                'filePath': scriptEditor.filePath(),
                'code': scriptEditor.code()
            },
            serialize
        )

    def __updateTabStatus(self, tabIndex):
        """
        Utility method used to update the code editor tab status.
        """
        scriptEditor = self.widget(tabIndex)
        if not scriptEditor or not scriptEditor.filePath():
            return

        modified = scriptEditor.isModified()
        self.tabBar().setTabTextColor(
            tabIndex,
            QtGui.QColor(152, 195, 121) if modified else QtGui.QColor('')
        )

        if scriptEditor.filePath():
            self.setTabText(tabIndex, pathlib.Path(scriptEditor.filePath()).name)

        self.setTabToolTip(
            tabIndex,
            scriptEditor.filePath() + (' (Unsaved)' if modified else '') if scriptEditor.filePath() else ''
        )

class _ScriptEditorTabBarWidget(QtWidgets.QTabBar):
    """
    Custom tab bar widget used in the ScriptEditorTabWidget.
    """
    tabRenamed = QtCore.Signal(int)

    def removeCloseButton(self, index):
        """
        Remove the close button for a specific tab.
        """
        self.setTabButton(index, QtWidgets.QTabBar.RightSide, None)

    def contextMenuEvent(self, event):
        """
        Handle the right-click context menu on the tab bar.
        """
        index = self.tabAt(event.pos())
        self.setCurrentIndex(index)

        if not isinstance(self.parent().widget(index), ScriptEditorWidget):
            return

        scriptEditor = self.parent().widget(index)

        menu = QtWidgets.QMenu(self)

        clearOutputAction = QtWidgets.QAction("Clear output", self)
        menu.addAction(clearOutputAction)

        renameAction = None
        reloadAction = None
        diffAction = None
        revealAction = None
        copyPathAction = None
        saveAsAction = None
        saveAction = QtWidgets.QAction("Save file", self)
        menu.addAction(saveAction)
        if scriptEditor.filePath():
            saveAsAction = QtWidgets.QAction("Save file as...", self)
            menu.addAction(saveAsAction)

            reloadAction = QtWidgets.QAction("Reload file", self)
            menu.addAction(reloadAction)

            diffAction = QtWidgets.QAction("Diff changes", self)
            menu.addAction(diffAction)

            revealAction = QtWidgets.QAction("Reveal in file manager", self)
            menu.addAction(revealAction)

            copyPathAction = QtWidgets.QAction("Copy path to clipboard", self)
            menu.addAction(copyPathAction)
        else:
            renameAction = QtWidgets.QAction("Rename tab", self)
            menu.addAction(renameAction)

        action = menu.exec_(self.mapToGlobal(event.pos()))

        # rename
        if renameAction and action == renameAction:
            newName, ok = QtWidgets.QInputDialog.getText(
                self,
                "Rename tab",
                "Enter new tab name:", text=self.tabText(index)
            )
            if ok and newName:
                self.setTabText(index, newName)

                # emitting a signal about the tab has been renamed
                self.tabRenamed.emit(index)

        # clear output
        elif clearOutputAction and action == clearOutputAction:
            scriptEditor.setOutputDisplay(True)
            scriptEditor.clearOutput()

        # copy path to clipboard
        elif copyPathAction and action == copyPathAction:
            QtWidgets.QApplication.clipboard().setText(scriptEditor.filePath())

        # reveal in file manager
        elif revealAction and action == revealAction:
            task = Task.create('revealInFileManager')
            task.add(FsElement.createFromPath(scriptEditor.filePath()))
            task.output()

        # reload file
        elif reloadAction and action == reloadAction:
            scriptEditor.loadFile()
            self.tabRenamed.emit(index)

        # diff
        elif diffAction and action == diffAction:
            currentChanges = scriptEditor.code().splitlines()
            fileLines = []
            if scriptEditor.filePath():
                with open(scriptEditor.filePath()) as f:
                    fileLines = f.read().splitlines()

            diffOutput = []
            for line in difflib.unified_diff(fileLines, currentChanges, fromfile=scriptEditor.filePath(), tofile='Script Editor Session'):
                diffOutput.append(line)

            scriptEditor.setOutputDisplay(True)
            scriptEditor.outputWidget().append('\n'.join(diffOutput) if diffOutput else 'Diff: No changes were found.')

        # save current script
        elif saveAction and action == saveAction:
            scriptEditor.saveFile()

        # save as current script
        elif saveAsAction and action == saveAsAction:
            scriptEditor.saveFile(ignoreCurrentFilePath=True)

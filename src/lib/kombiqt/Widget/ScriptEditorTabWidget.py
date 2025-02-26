import functools
from Qt import QtWidgets, QtCore
from kombi.Config import Config
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

    def __init__(self, mainWidget=None, loadUserTabs=True, parent=None):
        """
        Create ScriptEditorWidget object.
        """
        super().__init__(parent=parent)
        self.setTabBar(_ScriptEditorTabBarWidget())
        self.setTabsClosable(True)
        self.setMovable(True)

        if mainWidget:
            self.__setMainWidget(mainWidget)

        if loadUserTabs:
            self.__loadUserTabs()

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
        self.setCornerWidget(scriptEditorButton, corner=QtCore.Qt.TopRightCorner)

        self.displayUpdate()

    def mainWidget(self):
        """
        Return the main widget associated with the script editor tab widget or None.
        """
        return self.__mainWidget

    def addScriptEditor(self, code="", tabName="Script Editor", setFocus=True):
        """
        Add a new script editor tab to the widget.
        """
        codeEditor = ScriptEditorWidget()
        codeEditor.setCode(code)
        tabIndex = self.addTab(codeEditor, Resource.icon("icons/python.png"), tabName)
        self.displayUpdate()
        codeEditor.codeChanged.connect(functools.partial(self.__onCodeChanged, tabIndex))

        if setFocus:
            self.setCurrentIndex(tabIndex)

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
        for keyName in self.__scriptEditorsConfig.keys():
            if not keyName.isdigit():
                continue
            tabInfo = self.__scriptEditorsConfig.value(keyName)
            self.addScriptEditor(tabInfo['code'], tabInfo['label'], setFocus=False)

    def __onTabClose(self, index):
        """
        Triggered when tab close button is pressed.
        """
        self.removeTab(index)

        self.__bakeTabs()

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
        codeEditor = self.widget(tabIndex)
        tabName = self.tabText(tabIndex)

        self.__scriptEditorsConfig.setValue(
            str(tabIndex),
            {
                'label': tabName,
                'code': codeEditor.code()
            },
            serialize
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

        if not isinstance(self.parent().widget(index), ScriptEditorWidget):
            return

        menu = QtWidgets.QMenu(self)
        renameAction = QtWidgets.QAction("Rename Tab", self)

        menu.addAction(renameAction)
        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == renameAction:
            newName, ok = QtWidgets.QInputDialog.getText(
                self,
                "Rename Tab",
                "Enter new tab name:", text=self.tabText(index)
            )
            if ok and newName:
                self.setTabText(index, newName)

                # emitting a signal about the tab has been renamed
                self.tabRenamed.emit(index)

import functools
from Qt import QtCore, QtWidgets, QtGui
from kombi.Config import Config
from kombi.Element import Element
from ..Resource import Resource

class ElementLevelNavigationWidget(QtWidgets.QFrame):
    """
    Display the elements as individual buttons side by side.
    """
    levelClicked = QtCore.Signal(object)
    levelContextMenu = QtCore.Signal(object)

    def __init__(self, showBookmarks=True) -> None:
        """
        Create a ElementLevelNavigationWidget object.
        """
        super(ElementLevelNavigationWidget, self).__init__()
        self.setObjectName('elementLevelNavigation')
        self.__elements = []
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setShowBookmarks(showBookmarks)
        self.__bookmarksConfig = Config('elementsLevelNavigationBookmarks')

        self.refresh()

    def setShowBookmarks(self, display):
        """
        Tells if the bookmarks button should be display on the navigation bar.
        """
        self.__displayBookmarks = display

    def showBookmarks(self):
        """
        Return if the bookmarks button is being displayed.
        """
        return self.__displayBookmarks

    def refresh(self):
        """
        Refresh the render of levels displayed in the widget.
        """
        self.__deleteItemsOfLayout(self.layout())
        navigationLayout = QtWidgets.QHBoxLayout()
        navigationLayout.setSpacing(2)

        for element in self.__elements:
            elementNavigationButton = _LevelPushButton(element.tag('label'))
            elementNavigationButton.setFlat(True)
            elementNavigationButton.clicked.connect(functools.partial(self.__onNavigationClicked, element))
            elementNavigationButton.contextMenu.connect(functools.partial(self.__onNavigationContextMenu, element))

            iconPath = element.tag('icon') if 'icon' in element.tagNames() else None
            if iconPath:
                elementNavigationButton.setIcon(
                    Resource.icon(iconPath)
                )

            navigationLayout.addWidget(elementNavigationButton, 10)
            if element != self.__elements[-1]:
                navigationLayout.addWidget(QtWidgets.QLabel('/'))

        navigationLayout.addStretch(1000)
        self.layout().addLayout(navigationLayout)

        if self.showBookmarks() and self.elements():
            currentLevel = '/'.join(map(lambda x: x.var('name'), self.elements()))
            bookmarkIcon = 'icons/bookmark.png'
            if currentLevel in self.__bookmarks():
                bookmarkIcon = 'icons/addedToBookmark.png'
            bookmarksButton = QtWidgets.QPushButton(Resource.icon(bookmarkIcon), '')
            bookmarksButton.setFlat(True)
            bookmarksButton.setToolTip('Bookmarks')
            bookmarksButton.clicked.connect(self.__displayBookmarksMenu)
            self.layout().addWidget(bookmarksButton)

    def setElements(self, elements):
        """
        Set the elements that will be displayed in this widget.
        """
        for element in elements:
            assert isinstance(element, Element), "Invalid element type!"

        self.__elements = elements
        self.refresh()

    def elements(self):
        """
        Return the list of elements displayed by this widget.
        """
        return self.__elements

    def gotoPath(self, fullPath):
        """
        Change the level to the input fullPath.
        """
        levelNames = fullPath.split('/')[1:]
        newLevelElements = [self.elements()[0]]
        for levelName in levelNames:
            found = False
            for childLevel in newLevelElements[-1].children():
                if childLevel.var('name') == levelName:
                    newLevelElements.append(childLevel)
                    found = True
                    break

            if not found:
                break

        self.setElements(newLevelElements)
        self.__onNavigationClicked(newLevelElements[-1])

        return newLevelElements[-1]

    def __displayBookmarksMenu(self):
        """
        Triggered when bookmarks button is pressed.
        """
        if not self.elements():
            return

        menu = QtWidgets.QMenu(self)

        currentLevel = '/'.join(map(lambda x: x.var('name'), self.elements()))
        if currentLevel in self.__bookmarks():
            action = menu.addAction('Remove current from Bookmarks')
            action.triggered.connect(self.__removeFromBookmark)
        else:
            action = menu.addAction('Add current to Bookmarks')
            action.triggered.connect(self.__addToBookmark)

        menu.addSeparator()

        for bookmark in self.__bookmarks():
            if not bookmark.startswith(self.elements()[0].var('name') + '/'):
                continue

            action = menu.addAction(bookmark)
            action.triggered.connect(functools.partial(self.gotoPath, bookmark))

        menu.exec_(QtGui.QCursor.pos())

    def __addToBookmark(self):
        """
        Add the current level to the config.
        """
        fullLevelPath = '/'.join(map(lambda x: x.var('name'), self.elements()))
        rootType = self.__elements[0].var('type')

        bookmarks = []
        if self.__bookmarksConfig.hasKey(rootType):
            bookmarks = self.__bookmarksConfig.value(rootType)

        if fullLevelPath in bookmarks:
            bookmarks.remove(fullLevelPath)

        bookmarks.insert(0, fullLevelPath)
        self.__bookmarksConfig.setValue(rootType, bookmarks)

        self.refresh()

    def __removeFromBookmark(self):
        """
        Remove the current level from the config.
        """
        fullLevelPath = '/'.join(map(lambda x: x.var('name'), self.elements()))
        rootType = self.__elements[0].var('type')

        bookmarks = []
        if self.__bookmarksConfig.hasKey(rootType):
            bookmarks = self.__bookmarksConfig.value(rootType)

        if fullLevelPath in bookmarks:
            bookmarks.remove(fullLevelPath)

        self.__bookmarksConfig.setValue(rootType, bookmarks)

        self.refresh()

    def __bookmarks(self):
        """
        Returns a list of all bookmarks.
        """
        if not self.elements():
            return []

        rootType = self.__elements[0].var('type')
        bookmarks = []
        if self.__bookmarksConfig.hasKey(rootType):
            bookmarks = self.__bookmarksConfig.value(rootType)

        return bookmarks

    def __onNavigationClicked(self, element):
        """
        Emit the level clicked signal.
        """
        self.levelClicked.emit(element)

    def __onNavigationContextMenu(self, element):
        """
        Emit the level context menu signal.
        """
        self.levelContextMenu.emit(element)

    def __deleteItemsOfLayout(self, layout):
        """
        Utility method to remove all widgets in the layout.
        """
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.__deleteItemsOfLayout(item.layout())


class _LevelPushButton(QtWidgets.QPushButton):
    """
    Internal QPushButton re-implementation to provide a signal for the context menu (right click).
    """
    contextMenu = QtCore.Signal()

    def mouseReleaseEvent(self, event):
        """
        In case the right button is pressed we emit the context menu signal.
        """
        if event.button() == QtCore.Qt.RightButton:
            self.contextMenu.emit()
        else:
            super().mouseReleaseEvent(event)

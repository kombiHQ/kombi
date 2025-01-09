import os
import hashlib
import functools
import weakref
from kombi.Element import Element
from kombi.Template import Template
from kombi.Config import Config
from ..Widget.ComboBoxInputDialog import ComboBoxInputDialog
from ..Widget.RunTaskHoldersWidget import RunTaskHoldersWidget
from ..Resource import Resource
from Qt import QtWidgets, QtGui, QtCore

class ElementListWidget(QtWidgets.QTreeWidget):
    """
    Widget used to list elements.
    """

    def __init__(self):
        """
        Create a ElementListWidget object.
        """
        super().__init__()

        self.__showVars = False
        self.__showTags = False
        self.__checkableState = None
        self.__ignoreCheckedEvents = False
        self.__overridePreviousSelectedLocation = None

        self.setAlternatingRowColors(True)

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QTreeWidget.SelectItems)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.itemChanged.connect(self.__onSourceTreeItemCheckedChanged)
        self.customContextMenuRequested.connect(self.__onSourceTreeContextMenu)

        header = QtWidgets.QTreeWidgetItem([])
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.setHeaderItem(header)

        self.setIconSize(QtCore.QSize(32, 32))
        self.__taskHolders = []
        self.__uiHintSourceColumns = []

        # TODO
        self.__checkedViewMode = "Group"

    def setup(self, taskHolders):
        """
        Define the task holders used to filter the elements.
        """
        self.__taskHolders = taskHolders[:]

        if self.__taskHolders and self.__taskHolders[0].hasVar('configDirectory'):
            configDirectory = self.__taskHolders[0].var('configDirectory')
            configSignature = hashlib.md5(configDirectory.encode()).hexdigest()
            self.__overridesConfig = Config(configSignature, 'taskOverrides')
            self.__overridesConfig.setValue('configDirectory', configDirectory, serialize=False)
        else:
            self.__overridesConfig = None

        self.__updateSourceColumns(self.__taskHolders)

    def selectedElements(self):
        """
        Return a list of selected elements.
        """
        selectedElements = set()
        for selectedIndex in self.selectionModel().selectedIndexes():
            selectedItem = self.itemFromIndex(selectedIndex)

            elements = []
            if hasattr(selectedItem, 'elements'):
                elements = selectedItem.elements[:]
            if not elements:
                continue

            selectedElements.update(elements)

        return list(selectedElements)

    def updateElementList(self, elementList):
        """
        Update the elements displayed in the source tree.
        """
        elementTypes = set()
        elementTags = {}

        # workaround necessary to improve the rendering speed
        self.setVisible(False)

        # group
        if self.__checkedViewMode == "Group":
            groupedElements = self.__groupElements(elementList)

            for groupName in groupedElements.keys():
                if groupName:
                    parent = QtWidgets.QTreeWidgetItem(self)
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
                            self,
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

                child = self.__createSourceTreeChildItem(element, self, elementTypes, elementTags)

                if self.__checkableState is not None:
                    child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
                    child.setCheckState(0, QtCore.Qt.Checked if self.__checkableState else QtCore.Qt.Unchecked)

                self.__addSourceTreeColumnData(element, child)

        # workaround to improve the performance of the rendering:
        # restoring the visibility of the widget
        self.setVisible(True)

        # TODO:
        # for elementType in sorted(elementTypes):
        #     action = self.__elementTypesMenu.addAction(elementType)
        #     action.setCheckable(True)
        #     action.setChecked(True)
        #     action.changed.connect(self.__onSourceFiltersChanged)

        self.resizeColumnToContents(0)

    def __onSourceTreeContextMenu(self, point=None):
        """
        Slot triggered when context menu from source tree is triggered.
        """
        self.resizeColumnToContents(0)

        selectedIndexes = self.selectionModel().selectedIndexes()
        if not selectedIndexes:
            return

        selectedColumn = selectedIndexes[0].column()
        menu = QtWidgets.QMenu(self)
        subMenus = {}
        if selectedColumn == 0:
            elements = self.selectedElements()
            for index, taskHolder in enumerate(self.__taskHolders):
                filteredElements = []
                for element in elements:
                    if not taskHolder.matcher().match(element):
                        continue
                    filteredElements.append(element)

                if not filteredElements or taskHolder.task().hasMetadata('ui.task.showInContextMenu') and not taskHolder.task().metadata('ui.task.showInContextMenu'):
                    continue

                taskName = Template.runProcedure('camelcasetospaced', taskHolder.task().metadata('name'))
                if taskHolder.task().hasMetadata('ui.task.showExecutionSettings') and not taskHolder.task().metadata('ui.task.showExecutionSettings'):
                    pass
                else:
                    taskName += ' ...'

                currentMenu = menu
                # building submenus in case the "ui.task.menuPath" is defined (levels separated by '/')
                if taskHolder.task().hasMetadata('ui.task.menuPath'):
                    currentLevel = ''
                    for level in taskHolder.task().metadata('ui.task.menuPath').split('/'):
                        if not level:
                            continue
                        currentLevel += f'/{level}'
                        if currentLevel not in subMenus:
                            newLevel = QtWidgets.QMenu(level)
                            currentMenu.addMenu(newLevel)
                            subMenus[currentLevel] = newLevel
                        currentMenu = subMenus[currentLevel]

                # adding a separator when 'ui.task.menuSeparator' is defined
                if taskHolder.task().hasMetadata('ui.task.menuSeparator') and taskHolder.task().metadata('ui.task.menuSeparator'):
                    currentMenu.addSeparator()

                actionArgs = []
                # in case there is an icon defined by the "ui.task.menuIcon" metadata
                if taskHolder.task().hasMetadata('ui.task.menuIcon'):
                    actionArgs.append(Resource.icon(taskHolder.task().metadata('ui.task.menuIcon')))
                actionArgs.append(taskName)
                action = currentMenu.addAction(*actionArgs)
                action.triggered.connect(functools.partial(self.__onRunTaskHolder, index, filteredElements))
        elif self.__checkableState is not None:
            action = menu.addAction('Override Value')
            action.triggered.connect(self.__onChangeElementValue)

            action = menu.addAction('Reset Value')
            action.triggered.connect(self.__onResetElementValue)

        if len(menu.actions()):
            menu.exec_(self.mapToGlobal(point) if point is not None else QtGui.QCursor.pos())

    def __onRunTaskHolder(self, index, elements):
        """
        Slog triggered by the context menu action to run the task holders.
        """
        if RunTaskHoldersWidget.run([self.__taskHolders[index]], elements, parent=self):
            self.__onRefreshSourceDir(force=True)

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

            self.setHeaderItem(
                header
            )

    def __createSourceTreeChildItem(self, element, parent, elementTypes, elementTags):
        """
        Create a new child item in the source tree.
        """
        child = QtWidgets.QTreeWidgetItem(parent)
        child.elements = [element]
        self.__updateIcon(child, element)

        # visible data
        child.setData(0, QtCore.Qt.EditRole, element.var('name') + '   ')
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

    def __addSourceTreeColumnData(self, element, treeItem, groupedElements=None):
        """
        Add element information to a column in the source tree.
        """
        overrides = {}
        if self.__overridesConfig and self.__overridesConfig.hasKey('overrides'):
            overrides = self.__overridesConfig.value('overrides')

        # adding column information
        for index, column in enumerate(self.__uiHintSourceColumns):

            hasOverride = False
            value = ''
            columnLabel = ''
            mixedValues = False
            for elementIndex, checkElement in enumerate(groupedElements if groupedElements else [element]):
                currentValue = ''

                if checkElement.var('fullPath') in overrides and column in overrides[checkElement.var('fullPath')]:
                    currentValue = overrides[checkElement.var('fullPath')][column]
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

    def __onSourceTreePresetsClicked(self, treeItemWeakRef, columnIndex):
        """
        Slot triggered when the preset arrow button is clicked.
        """
        currentIndex = self.indexFromItem(treeItemWeakRef(), columnIndex)

        # resetting the selection in case the clicked item is not part of
        # the selection
        if currentIndex not in self.selectionModel().selectedIndexes():
            self.selectionModel().select(currentIndex, QtCore.QItemSelectionModel.SelectCurrent)

        self.__onChangeElementValue()

    def __onResetElementValue(self):
        """
        Slot triggered when an override in the source tree is removed.
        """
        overrides = {}
        if self.__overridesConfig and self.__overridesConfig.hasKey('overrides'):
            overrides = dict(self.__overridesConfig.value('overrides'))

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

        if self.__overridesConfig:
            self.__overridesConfig.setValue('overrides', overrides)
            self.__onRefreshSourceDir()

    def __onChangeElementValue(self):
        """
        Slot triggered when an override in the source tree is triggered.
        """
        value = None
        overrides = {}
        if self.__overridesConfig and self.__overridesConfig.hasKey('overrides'):
            overrides = dict(self.__overridesConfig.value('overrides'))

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
                                elements[0].var('name')
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

        if self.__overridesConfig:
            self.__overridesConfig.setValue('overrides', overrides)

        if value is not None:
            self.__onRefreshSourceDir()

    def __groupElements(self, elements):
        """
        Return a dictionary containing the matched elements grouped.
        """
        groupedElements = {}
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
        if not self.selectionModel().selectedIndexes() or self.__ignoreCheckedEvents:
            return

        self.__ignoreCheckedEvents = True

        for selectedIndex in self.selectionModel().selectedIndexes():
            selectedItem = self.itemFromIndex(selectedIndex)

            if hasattr(selectedItem, 'elements'):
                selectedItem.setCheckState(0, currentItem.checkState(0))

        self.__ignoreCheckedEvents = False

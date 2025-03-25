import os
import hashlib
import functools
import traceback
import weakref
from kombi.Element import Element
from kombi.Template import Template
from kombi.Config import Config
from kombi.Element import ElementContext
from ..Menu.TasksMenu import TasksMenu
from ..Resource import Resource
from Qt import QtWidgets, QtGui, QtCore


class ElementListWidget(QtWidgets.QTreeWidget):
    """
    Widget used to list elements.
    """
    viewModes = ('group', 'flat')
    modifed = QtCore.Signal()
    parentContextMenu = QtCore.Signal()

    def __init__(self, defaultIconSize=Resource.listIconSize()):
        """
        Create a ElementListWidget object.
        """
        super().__init__()

        self.__showVars = False
        self.__showTags = False
        self.__checkableState = None
        self.__ignoreCheckedEvents = False
        self.__overridesConfig = None
        self.__overridePreviousSelectedLocation = None
        self.__verticalSourceScrollBarLatestPos = 0

        self.setAlternatingRowColors(True)

        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QTreeWidget.SelectItems)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.itemChanged.connect(self.__onSourceTreeItemCheckedChanged)
        self.customContextMenuRequested.connect(self.__onSourceTreeContextMenu)

        header = QtWidgets.QTreeWidgetItem([])
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.setHeaderItem(header)

        # the icon size can be potentially overridden by the element tag uiHintIconSize
        # assigned to the task holder
        self.setIconSize(QtCore.QSize(defaultIconSize, defaultIconSize))
        self.__taskHolders = []
        self.__columns = []

        self.__viewMode = 'group'

    def setShowVars(self, display):
        """
        Set the display of the variables.
        """
        self.__showVars = display
        self.modifed.emit()

    def showVars(self):
        """
        Return the display of the variables.
        """
        return self.__showVars

    def setShowTags(self, display):
        """
        Set the display of the tags.
        """
        self.__showTags = display
        self.modifed.emit()

    def showTags(self):
        """
        Return the display of the tags.
        """
        return self.__showTags

    def setViewMode(self, viewMode):
        """
        Change the view mode.
        """
        assert viewMode in self.viewModes, "Invalid view mode"
        self.__viewMode = viewMode
        self.modifed.emit()

    def viewMode(self):
        """
        Return the current view mode.
        """
        return self.__viewMode

    def setCheckableState(self, state):
        """
        Define the checkable state for the widget (Boolean for the default state and None for no state)..
        """
        self.__checkableState = state

        if state is not None:
            self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        else:
            self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

    def checkableState(self):
        """
        Return the checkable state.
        """
        return self.__checkableState

    def setup(self, taskHolders):
        """
        Define the task holders used to filter the elements.
        """
        self.__taskHolders = taskHolders[:]
        self.__overridesConfig = None

        if taskHolders:
            for taskHolder in self.__taskHolders:
                if 'uiHintIconSize' in taskHolder.tagNames():
                    iconSize = taskHolder.tag('uiHintIconSize')
                    self.setIconSize(QtCore.QSize(iconSize, iconSize))

                if 'uiHintCheckedByDefault' in taskHolder.tagNames():
                    self.setCheckableState(taskHolder.tag('uiHintCheckedByDefault'))

                if 'configDirectory' in taskHolder.varNames():
                    configDirectory = taskHolder.var('configDirectory')
                    configSignature = hashlib.md5(configDirectory.encode()).hexdigest()
                    self.__overridesConfig = Config(configSignature, 'taskOverrides')
                    self.__overridesConfig.setValue('configDirectory', configDirectory, serialize=False)

        self.__updateColumns(self.__taskHolders)

    def refresh(self):
        """
        Refresh the element list.
        """
        self.__verticalSourceScrollBarLatestPos = self.verticalScrollBar().value()
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        # collecting the current state of the tree
        treeData = {}
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            treeData[(index, item.text(0))] = {
                "checked": item.checkState(0),
                "expanded": item.isExpanded()
            }

        # reapplying the state
        for index in range(self.topLevelItemCount()):
            item = self.topLevelItem(index)
            key = (index, item.text(0))

            if key in treeData:
                if self.__checkableState is not None and bool(item.flags() & QtCore.Qt.ItemIsUserCheckable):
                    item.setCheckState(0, treeData[key]["checked"])
                item.setExpanded(treeData[key]["expanded"])

        # workaround necessary to restore the position of the scrollbar
        QtCore.QTimer.singleShot(0, self.__onRestoreVerticalScrollBar)

    def checkedElements(self, applyOverrides=True):
        """
        Return a list of checked elements in the tree.
        """
        totalRows = self.model().rowCount()
        result = []
        for i in range(totalRows):
            self.model().index(i, 0)
            item = self.topLevelItem(i)

            # collections
            if not isinstance(item, ElementsTreeWidgetItem):
                for childIndex in range(item.childCount()):
                    childItem = item.child(childIndex)
                    if childItem.checkState(0) and isinstance(childItem, ElementsTreeWidgetItem):
                        result.extend(childItem.elements())

            # root items
            elif item.checkState(0) and isinstance(item, ElementsTreeWidgetItem):
                result.extend(item.elements())

        result = list(map(lambda x: x.clone(), result))
        if applyOverrides:
            self.__applySourceOverrides(result)
        return result

    def selectedElements(self, applyOverrides=True):
        """
        Return a list of selected elements.
        """
        selectedElements = set()
        for selectedIndex in self.selectionModel().selectedIndexes():
            selectedItem = self.itemFromIndex(selectedIndex)

            elements = []
            if isinstance(selectedItem, ElementsTreeWidgetItem):
                elements = selectedItem.elements()[:]
            if not elements:
                continue

            selectedElements.update(elements)

        result = list(selectedElements)
        if applyOverrides:
            self.__applySourceOverrides(result)
        return result

    def elements(self, applyOverrides=True):
        """
        Return the elements displayed in the tree.
        """
        totalRows = self.model().rowCount()
        result = []
        for i in range(totalRows):
            self.model().index(i, 0)
            item = self.topLevelItem(i)

            # collections
            if not isinstance(item, ElementsTreeWidgetItem):
                for childIndex in range(item.childCount()):
                    childItem = item.child(childIndex)
                    if isinstance(childItem, ElementsTreeWidgetItem):
                        result.extend(childItem.elements())

            # root items
            elif isinstance(item, ElementsTreeWidgetItem):
                result.extend(item.elements())

        result = list(map(lambda x: x.clone(), result))
        if applyOverrides:
            self.__applySourceOverrides(result)
        return result

    def setElements(self, elementList):
        """
        Update the elements displayed in the tree.
        """
        self.clear()

        elementTypes = set()
        elementTags = {}

        # workaround necessary to improve the rendering speed
        self.setVisible(False)

        # group
        if self.__viewMode == "group":
            groupedElements = self.__groupElements(elementList)

            for groupName in groupedElements.keys():
                if groupName:
                    parent = ElementsTreeWidgetItem(self)
                    self.__updateIcon(parent, groupedElements[groupName][0])
                    parent.setElements(list(groupedElements[groupName]))

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

        self.resizeColumnToContents(0)

    def __applySourceOverrides(self, elements):
        """
        Apply overrides overrides on the tree.
        """
        overrides = {}
        if self.__overridesConfig and self.__overridesConfig.hasKey('overrides'):
            overrides = self.__overridesConfig.value('overrides')

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

    def __onSourceTreeContextMenu(self, point=None):
        """
        Slot triggered when context menu from tree is triggered.
        """
        self.resizeColumnToContents(0)

        selectedIndexes = self.selectionModel().selectedIndexes()
        if not selectedIndexes:
            self.parentContextMenu.emit()
            return

        selectedColumn = selectedIndexes[0].column()
        menu = TasksMenu(self.__taskHolders, parent=self)
        menu.executed.connect(self.__onRunTaskHolder)
        if selectedColumn == 0:
            menu.addElements(self.selectedElements())

        elif self.__checkableState is not None:
            action = menu.addAction('Override Value')
            action.triggered.connect(self.__onChangeElementValue)

            action = menu.addAction('Reset Value')
            action.triggered.connect(self.__onResetElementValue)

        if len(menu.actions()):
            menu.exec_(self.mapToGlobal(point) if point is not None else QtGui.QCursor.pos())

    def __onRunTaskHolder(self):
        """
        Slog triggered by the context menu action to run the task holders.
        """
        self.modifed.emit()

    def __updateColumns(self, taskHolders):
        """
        Update the widget columns.
        """
        # updating columns
        columns = []
        for taskHolder in filter(lambda x: 'uiHintColumns' in x.tagNames(), taskHolders):
            for columnName in filter(lambda x: x not in columns, taskHolder.tag('uiHintColumns')):
                columns.append(columnName)

        # fix-me: workaround necessary to avoid the bug of not showing
        # the options properly inside of the execution settings
        if not len(columns):
            columns.append(' ')

        if columns != self.__columns:
            self.__columns = columns
            header = QtWidgets.QTreeWidgetItem(
                [''] + list(map(lambda x: Template.runProcedure('camelcasetospaced', x), self.__columns))
            )

            self.setHeaderItem(
                header
            )

    def __createSourceTreeChildItem(self, element, parent, elementTypes, elementTags):
        """
        Create a new child item in the tree.
        """
        child = ElementsTreeWidgetItem(parent)
        child.setElements([element])
        self.__updateIcon(child, element)

        # visible data
        child.setData(0, QtCore.Qt.EditRole, element.tag('label') + '   ')
        self.__addSourceTreeColumnData(element, child)

        elementTypes.add(element.var('type'))

        if self.__showVars:
            variables = ElementsTreeWidgetItem(child)
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
            tags = ElementsTreeWidgetItem(child)
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
        Add element information to a column in the tree.
        """
        overrides = {}
        if self.__overridesConfig and self.__overridesConfig.hasKey('overrides'):
            overrides = self.__overridesConfig.value('overrides')

        # adding column information
        for index, column in enumerate(self.__columns):

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
                self.setItemWidget(treeItem, index + 1, columnButton)

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

                self.setItemWidget(treeItem, index + 1, presetsHolderWidget)

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
        Slot triggered when an override in the tree is removed.
        """
        overrides = {}
        if self.__overridesConfig and self.__overridesConfig.hasKey('overrides'):
            overrides = dict(self.__overridesConfig.value('overrides'))

        selectedElements = set()
        columnNames = set()
        for selectedIndex in self.selectionModel().selectedIndexes():
            selectedItem = self.itemFromIndex(selectedIndex)

            elements = []
            if isinstance(selectedItem, ElementsTreeWidgetItem):
                elements = selectedItem.elements()[:]
            if not elements:
                continue

            selectedColumn = selectedIndex.column()
            columnName = self.__columns[selectedColumn - 1]

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
            self.modifed.emit()

    def __onChangeElementValue(self):
        """
        Slot triggered when an override in the tree is triggered.
        """
        value = None
        overrides = {}
        if self.__overridesConfig and self.__overridesConfig.hasKey('overrides'):
            overrides = dict(self.__overridesConfig.value('overrides'))

        for selectedIndex in self.selectionModel().selectedIndexes():
            selectedItem = self.itemFromIndex(selectedIndex)

            elements = []
            if isinstance(selectedItem, ElementsTreeWidgetItem):
                elements = selectedItem.elements()[:]
            if not elements:
                continue

            selectedColumn = selectedIndex.column()
            columnName = self.__columns[selectedColumn - 1]

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
                    promptDialog = _ComboBoxInputDialog(
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
                                elements[0].tag('label')
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
            self.modifed.emit()

    def __groupElements(self, elements):
        """
        Return a dictionary containing the matched elements grouped.
        """
        groupedElements = {}
        groupedElements[None] = []
        for elementList in Element.group(elements):
            for element in elementList:
                # group
                if self.__viewMode == 'group' and 'group' in element.tagNames():
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

        iconOverlayPath = element.tag('iconOverlay') if 'iconOverlay' in element.tagNames() else None
        if iconOverlayPath:
            icon = Resource.mergePixmap(
                Resource.pixmap(iconPath, self.iconSize().width(), self.iconSize().height()),
                Resource.pixmap(iconOverlayPath, self.iconSize().width(), self.iconSize().height()),
                resultAsIcon=True
            )
        else:
            icon = Resource.icon(iconPath)

        item.setIcon(columnIndex, icon)

    def __onSourceTreeItemCheckedChanged(self, currentItem):
        """
        Slot triggered when the check state of an item in the tree is changed.
        """
        if not self.selectionModel().selectedIndexes() or self.__ignoreCheckedEvents:
            return

        self.__ignoreCheckedEvents = True

        for selectedIndex in self.selectionModel().selectedIndexes():
            selectedItem = self.itemFromIndex(selectedIndex)

            if isinstance(selectedItem, ElementsTreeWidgetItem):
                selectedItem.setCheckState(0, currentItem.checkState(0))

        self.__ignoreCheckedEvents = False

    def __onColumnButton(self, treeItemWeakRef, callableName):
        """
        Slot triggered when the column button is clicked.
        """
        elements = treeItemWeakRef().elements()

        # executing callable
        refresh = False
        for index, element in enumerate(elements):
            if hasattr(element, callableName):
                try:
                    if getattr(elements[0], callableName)(index, len(elements)):
                        refresh = True
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

        if refresh:
            self.modifed.emit()

    def __onRestoreVerticalScrollBar(self):
        """
        Slot triggered to restore the vertical scrollbar position.
        """
        self.verticalScrollBar().setSliderPosition(self.__verticalSourceScrollBarLatestPos)

class ElementsTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """
    Tree widget item implementation that supports elements.
    """
    def __init__(self, *args, **kwargs):
        """
        Create an ElementsTreeWidgetItem object.
        """
        super().__init__(*args, **kwargs)
        self.setElements([])

    def setElements(self, elements):
        """
        Set the elements associated with the item.
        """
        self.__elements = elements

    def elements(self):
        """
        Return the elements associated with the item.
        """
        return self.__elements

class _ComboBoxInputDialog(QtWidgets.QDialog):
    """
    Provides a generic combo box prompt dialog.
    """
    def __init__(self, presets=[], title="", helpText="", editable=True, minimumWidth=600, **kwargs):
        """
        Create a combo box input dialog object.
        """
        super(ComboBoxInputDialog, self).__init__(**kwargs)

        assert isinstance(presets, (list, tuple)), 'Invalid input list!'
        self.setWindowTitle(title)
        self.setMinimumWidth(minimumWidth)

        self.__comboBox = QtWidgets.QComboBox()
        for preset in presets:
            self.__comboBox.addItem(str(preset))
        self.__comboBox.setEditable(editable)
        self.__comboBox.completer().setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

        self.__buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.__buttonBox.accepted.connect(self.accept)
        self.__buttonBox.rejected.connect(self.reject)

        mainLayout = QtWidgets.QVBoxLayout()
        if helpText:
            mainLayout.addWidget(QtWidgets.QLabel(helpText), 0)

        mainLayout.addWidget(self.__comboBox)
        mainLayout.addWidget(self.__buttonBox)

        self.setLayout(mainLayout)

    def currentText(self):
        """
        Return the current text in the combo box.
        """
        return str(self.__comboBox.currentText())

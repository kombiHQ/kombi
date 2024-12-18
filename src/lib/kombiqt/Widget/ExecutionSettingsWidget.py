import os
import datetime
import functools
import traceback
import weakref
from .CheckComboBox import CheckComboBox
from ..Resource import Resource
from kombi.Element import Element
from kombi.Task import Task, TaskValidationError
from kombi.Template import Template
from kombi.ProcessExecution import ProcessExecution
from Qt import QtCore, QtWidgets, QtGui

class ExecutionSettingsWidgetError(Exception):
    """
    Base exception for execution settings widget error.
    """

class ExecutionSettingsWidgetRequiredError(ExecutionSettingsWidgetError):
    """
    Custom exception type raised when a required option is empty.
    """

    def __init__(self, message, task):
        """
        Create an execution settings widget required error object.
        """
        super(ExecutionSettingsWidgetRequiredError, self).__init__(message)
        assert isinstance(task, Task), "Invalid task type!"

        self.__task = task

    def task(self):
        """
        Return the task associated with the error.
        """
        return self.__task

class CustomTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, *args, **kwargs):
        super(CustomTreeWidget, self).__init__(*args, **kwargs)
        self.setFrameShape(QtWidgets.QFrame.WinPanel)

class ExecutionSettingsWidget(QtWidgets.QTreeWidget):
    """
    This widget is used to list the tasks options.
    """

    taskHolderOptionChangedSignal = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        """
        Create a ExecutionSettingsWidget object.
        """
        super(ExecutionSettingsWidget, self).__init__(*args, **kwargs)
        self.__messageBox = None
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.header().hide()

        header = QtWidgets.QTreeWidgetItem(['Target'])
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.setHeaderItem(header)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setUniformRowHeights(False)

        self.taskHolderOptionChangedSignal.connect(self.__onTaskHolderOptionChanged)

    def refresh(self, elements, taskHolders):
        """
        Update the execution settings.
        """
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.clear()

        self.setHeaderItem(
            QtWidgets.QTreeWidgetItem(
                ("", "")
            )
        )

        for index, taskHolder in enumerate(taskHolders):
            try:
                matchedElements = taskHolder.query(elements)
            except Exception as error:
                QtWidgets.QApplication.restoreOverrideCursor()
                traceback.print_exc()

                QtWidgets.QMessageBox.critical(
                    self,
                    "Template processing error",
                    "<nobr>" + str(error).replace("\n", "<br>") + "</nobr>",
                    QtWidgets.QMessageBox.Ok,
                )
                raise error

            if taskHolder.importTemplates():
                clonedTaskHolder = taskHolder.clone()
                child = self.__createTask(self, clonedTaskHolder)
                child.taskHolderIndex = index
                child.taskHolder = clonedTaskHolder
                continue

            alreadyFailed = False
            for elementList in Element.group(matchedElements):
                nameSuffix = "{} ({} total)".format(
                    elementList[0].tag('group') if 'group' in elementList[0].tagNames() else elementList[0].var('baseName'),
                    len(elementList)
                )

                clonedTaskHolder = taskHolder.clone()

                # checking if task has the setup method
                if hasattr(clonedTaskHolder.task(), 'setup') and \
                        hasattr(clonedTaskHolder.task().setup, '__call__'):

                    try:
                        clonedTaskHolder.task().setup(elementList)
                    except Exception as err:
                        traceback.print_exc()

                        if not alreadyFailed:
                            alreadyFailed = True
                            self.__messageBox = QtWidgets.QMessageBox(
                                self,
                                "Task '{}' setup error".format(
                                    clonedTaskHolder.task().type()
                                ),
                                QtWidgets.QMessageBox.Ok
                            )
                            self.__messageBox.setWindowModality(QtCore.Qt.NonModal)
                            self.__messageBox.setIcon(QtWidgets.QMessageBox.Critical)
                            self.__messageBox.setText(str(err))
                            self.__messageBox.setDetailedText(str(err))
                            self.__messageBox.show()

                matchedChild = self.__createTask(
                    self,
                    clonedTaskHolder,
                    nameSuffix
                )

                # TODO: this needs to change
                clonedTaskHolder.entry = weakref.ref(matchedChild)
                matchedChild.taskHolderIndex = index
                matchedChild.elementList = elementList
                matchedChild.taskHolder = clonedTaskHolder

                # option to enable the task holder
                matchedChild.setCheckState(0, QtCore.Qt.Checked)

                # emitting task holder option changed signal
                try:
                    self.taskHolderOptionChangedSignal.emit(clonedTaskHolder)
                except Exception:
                    traceback.print_exc()

        self.resizeColumnToContents(0)
        QtWidgets.QApplication.restoreOverrideCursor()

    def executionTaskHolders(self):
        """
        Return a list of task holders enabled and containing the modifications made by the user.
        """
        result = []

        for item in self.findItems('', QtCore.Qt.MatchContains):
            if item.checkState(0) == QtCore.Qt.Checked:

                # checking for required task options. In case we found a required task
                # with none value we will raise an exception
                for task in item.taskHolder.childTasks():

                    # running validations without any elements (this will allow validations
                    # that verify for options to take affect in all tasks)
                    try:
                        task.validate()
                    except TaskValidationError as err:
                        raise ExecutionSettingsWidgetRequiredError(
                            str(err),
                            task
                        )

                    for optionName in task.optionNames():
                        optionValue = task.option(optionName)
                        if optionValue is None:
                            continue

                        uiOptionMainName = 'ui.options.{}'.format(optionName)

                        # we look for the required metadata directly depending
                        # data type
                        if isinstance(optionValue, (list, tuple)):
                            for index, itemValue in enumerate(optionValue):
                                uiOptionMetadataName = "{}.items.{}.required".format(uiOptionMainName, index)
                                if task.hasMetadata(uiOptionMetadataName) and task.metadata(uiOptionMetadataName) and not itemValue:
                                    uiLabel = "{}.items.{}.label".format(uiOptionMainName, index)
                                    displayOptionName = task.metadata(uiLabel) if task.hasMetadata(uiLabel) else "{} at {}".format(optionName, index)
                                    raise ExecutionSettingsWidgetRequiredError(
                                        'Option "{}" is required (it cannot be empty)'.format(
                                            displayOptionName
                                        ),
                                        task
                                    )
                        elif isinstance(optionValue, dict):
                            for key, itemValue in optionValue.items():
                                uiOptionMetadataName = "{}.items.{}.required".format(uiOptionMainName, key)
                                if task.hasMetadata(uiOptionMetadataName) and task.metadata(uiOptionMetadataName) and not itemValue:
                                    uiLabel = "{}.items.{}.label".format(uiOptionMainName, key)
                                    displayOptionName = task.metadata(uiLabel) if task.hasMetadata(uiLabel) else "{} at {}".format(optionName, key)
                                    raise ExecutionSettingsWidgetRequiredError(
                                        'Option "{}" is required (it cannot be empty)'.format(
                                            displayOptionName
                                        ),
                                        task
                                    )
                        # scalar value
                        else:
                            uiOptionMetadataName = "{}.required".format(uiOptionMainName)
                            if task.hasMetadata(uiOptionMetadataName) and task.metadata(uiOptionMetadataName) and not optionValue:
                                uiLabel = "{}.label".format(uiOptionMainName)
                                displayOptionName = task.metadata(uiLabel) if task.hasMetadata(uiLabel) else optionName
                                raise ExecutionSettingsWidgetRequiredError(
                                    'Option "{}" is required (it cannot be empty)'.format(
                                        displayOptionName
                                    ),
                                    task
                                )

                # running validations
                try:
                    item.taskHolder.task().validate(item.elementList)
                except TaskValidationError as err:
                    raise ExecutionSettingsWidgetRequiredError(
                        str(err),
                        item.taskHolder.task()
                    )

                result.append((item.taskHolder, item.elementList))

        return result

    def execute(self, dispatcher, showOutput=True, showDispatchedMessage=True):
        """
        Execute the task holders.
        """
        if self.__messageBox:
            self.__messageBox.reject()
        if not self.model().rowCount():
            QtWidgets.QMessageBox.information(
                self,
                "Kombi",
                "There are no tasks available for the current selection!",
                QtWidgets.QMessageBox.Ok
            )
            return

        output = ''
        dispatchedMessage = ''
        try:
            for taskHolder, elementsGroup in self.executionTaskHolders():
                # default label
                label = "{}/{} [{}]".format(
                    os.path.basename(taskHolder.var('configDirectory')),
                    elementsGroup[0].tag('group') if 'group' in elementsGroup[0].tagNames() else elementsGroup[0].var('baseName'),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

                # custom label
                if taskHolder.task().hasMetadata('dispatch.label'):
                    label = Template(
                        "{} [{}]".format(
                            taskHolder.task().metadata('dispatch.label'),
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                    ).valueFromElement(elementsGroup[0])

                dispatcher.setOption('label', label)
                dispatchedMessage = dispatcher.option('dispatchedMessage')
                for result in dispatcher.dispatch(taskHolder, elementsGroup):
                    if isinstance(result, ProcessExecution):
                        output += result.stdoutContent()
                    else:
                        output += 'Dispatched to {}: {}'.format(dispatcher.type(), result)

        except Exception as err:
            traceback.print_exc()

            self.__messageBox = QtWidgets.QMessageBox(
                self,
                "Execution",
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

                self.__messageBox.show()
                return False

            self.__messageBox.show()
            raise err

        else:
            if showDispatchedMessage:
                QtWidgets.QMessageBox.information(
                    self,
                    "Execution",
                    dispatchedMessage,
                    QtWidgets.QMessageBox.Ok
                )

            if showOutput:
                self.__outputWidget = QtWidgets.QPlainTextEdit()
                self.__outputWidget.setPlainText(output)
                self.__outputWidget.setWindowTitle('Output')
                self.__outputWidget.setMinimumWidth(920)
                self.__outputWidget.setMinimumHeight(600)
                self.__outputWidget.setVisible(True)
                self.__outputWidget.setReadOnly(True)

        return True

    def __createSubtasks(self, parentEntry, taskHolder, mainOptions, path):
        """
        Create the sub tasks widget information.
        """
        if taskHolder.subTaskHolders():
            subTaskChild = QtWidgets.QTreeWidgetItem(parentEntry)
            subTaskChild.setData(0, QtCore.Qt.EditRole, 'Sub tasks')
            subTaskChild.setExpanded(False)

            for childTaskHolder in taskHolder.subTaskHolders():
                self.__createTask(subTaskChild, childTaskHolder, mainOptions=mainOptions, path=path)

    def __buildOptionWidget(self, taskHolder, optionName, value, assignTo, mainOptions):
        w = None
        signalWidget = None
        signal = None
        assignTo = list(assignTo)
        uiOptionMetadataName = 'ui.options.{}'.format(optionName)
        uiOptionVisualName = '{}.visual'.format(uiOptionMetadataName)

        # boolean type
        if isinstance(value, bool):
            w = QtWidgets.QCheckBox()
            w.setChecked(value)
            signal = w.stateChanged

        # array type used as check list
        elif isinstance(value, (list, tuple)) and taskHolder.task().hasMetadata(uiOptionVisualName) and \
                taskHolder.task().metadata(uiOptionVisualName) == 'checkList':
            w = CheckComboBox(self, placeholderText="None")
            model = w.model()

            values = []
            uiValuesListName = '{}.values'.format(uiOptionMetadataName)
            if taskHolder.task().hasMetadata(uiValuesListName):
                for value in taskHolder.task().metadata(uiValuesListName):
                    values.append(value)

            w.allValues = values
            for index, value in enumerate(values):
                w.addItem(str(value))

                if value in values:
                    model.item(index).setCheckable(True)
            signal = model.dataChanged

        # array type
        elif isinstance(value, (list, tuple)):
            w = CustomTreeWidget(self)
            w.setRootIsDecorated(False)
            w.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            w.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
            w.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            w.setColumnCount(2)
            w.header().hide()
            w.setMinimumHeight(200)
            w.setMaximumHeight(200)
            w.setAlternatingRowColors(True)

            for index, itemValue in enumerate(value):
                assignToItem = list(assignTo)
                assignToItem.append(index)

                # main option
                uiOptionMainName = 'ui.options.{}'.format(optionName)
                uiOptionMetadataName = "{}.items.{}.main".format(uiOptionMainName, '.'.join(map(str, assignToItem)))
                isMainOption = taskHolder.task().hasMetadata(uiOptionMetadataName) and taskHolder.task().metadata(uiOptionMetadataName)
                childItem = QtWidgets.QTreeWidgetItem(mainOptions if isMainOption else None)

                # label option
                uiOptionLabelName = "{}.items.{}.label".format(uiOptionMainName, '.'.join(map(str, assignToItem)))
                labelOption = taskHolder.task().metadata(uiOptionLabelName) if taskHolder.task().hasMetadata(uiOptionLabelName) and taskHolder.task().metadata(uiOptionLabelName) else Template.runProcedure('camelcasetospaced', str(index))

                # check custom label name option here
                childItem.setText(0, str(labelOption))
                w.addTopLevelItem(childItem)
                childWidget = self.__buildOptionWidget(taskHolder, optionName, itemValue, assignToItem, mainOptions)

                # check main option here
                if isMainOption:
                    self.setItemWidget(childItem, 1, childWidget)
                else:
                    w.setItemWidget(childItem, 1, childWidget)
            w.resizeColumnToContents(0)

        # hashmap type
        elif isinstance(value, dict):
            w = CustomTreeWidget(self)
            w.setRootIsDecorated(False)
            w.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            w.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
            w.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
            w.setColumnCount(2)
            w.header().hide()
            w.setMinimumHeight(200)
            w.setMaximumHeight(200)
            w.setAlternatingRowColors(True)

            for key, itemValue in value.items():
                assignToItem = list(assignTo)
                assignToItem.append(key)

                # main option
                uiOptionMainName = 'ui.options.{}'.format(optionName)
                uiOptionMetadataName = '{}.items.{}.main'.format(uiOptionMainName, '.'.join(map(str, assignToItem)))
                isMainOption = taskHolder.task().hasMetadata(uiOptionMetadataName) and taskHolder.task().metadata(uiOptionMetadataName)

                childItem = QtWidgets.QTreeWidgetItem(mainOptions if isMainOption else None)

                # label option
                uiOptionLabelName = '{}.items.{}.label'.format(uiOptionMainName, '.'.join(map(str, assignToItem)))
                labelOption = taskHolder.task().metadata(uiOptionLabelName) if taskHolder.task().hasMetadata(uiOptionLabelName) and taskHolder.task().metadata(uiOptionLabelName) else Template.runProcedure('camelcasetospaced', str(key))

                # check custom label name option here
                childItem.setText(0, str(labelOption))

                w.addTopLevelItem(childItem)
                childWidget = self.__buildOptionWidget(taskHolder, optionName, itemValue, assignToItem, mainOptions)

                # check main option here
                if isMainOption:
                    self.setItemWidget(childItem, 1, childWidget)
                else:
                    w.setItemWidget(childItem, 1, childWidget)

            w.resizeColumnToContents(0)

        # integer type
        elif isinstance(value, int):
            w = QtWidgets.QSpinBox()
            w.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            w.setMaximumWidth(150)
            w.setRange(-99999999, 99999999)
            w.setValue(value)
            signal = w.editingFinished

        # float type
        elif isinstance(value, float):
            w = QtWidgets.QDoubleSpinBox()
            w.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            w.setMaximumWidth(150)
            w.setRange(-99999999, 99999999)
            w.setValue(value)
            signal = w.editingFinished

        # string type
        else:
            uiOptionMetadataName = 'ui.options.{}'.format(optionName)
            if assignTo:
                uiOptionMetadataName = '{}.items.{}'.format(uiOptionMetadataName, '.'.join(map(str, assignTo)))

            uiOptionVisualName = '{}.visual'.format(uiOptionMetadataName)
            customVisual = taskHolder.task().metadata(uiOptionVisualName) if taskHolder.task().hasMetadata(uiOptionVisualName) else None

            if customVisual == 'longText':
                w = QtWidgets.QTextEdit(self)
                w.setMinimumHeight(100)
                w.setMaximumHeight(100)
                w.setPlainText(str(value))
                signal = w.textChanged

            elif customVisual == 'directoryPath':
                uiPresetListName = '{}.presets'.format(uiOptionMetadataName)
                presets = [
                    str(value)
                ]
                if taskHolder.task().hasMetadata(uiPresetListName):
                    for preset in taskHolder.task().metadata(uiPresetListName):
                        if preset in presets:
                            continue
                        presets.append(preset)

                editableWidget = QtWidgets.QComboBox(self) if len(presets) > 1 else QtWidgets.QLineEdit(str(value))
                editableWidget.setFocusPolicy(QtCore.Qt.ClickFocus)
                if len(presets) > 1:
                    editableWidget.addItems(presets)
                    editableWidget.setEditable(True)

                signalWidget = editableWidget
                signal = editableWidget.currentTextChanged if len(presets) > 1 else editableWidget.textChanged
                folderPicker = QtWidgets.QPushButton('Select Directory')
                folderPicker.clicked.connect(functools.partial(self.__onPickerSelectDir, editableWidget))
                folderPicker.setIcon(Resource.icon("icons/folder.png"))

                w = QtWidgets.QWidget(self)
                layout = QtWidgets.QHBoxLayout()
                layout.setContentsMargin(2, 2, 2, 2)
                layout.addWidget(editableWidget, 10)
                layout.addWidget(folderPicker, 0)
                w.setLayout(layout)

            elif customVisual == 'presets':
                w = QtWidgets.QComboBox(self)
                w.setFocusPolicy(QtCore.Qt.ClickFocus)

                presets = [
                    str(value)
                ]

                # preset list
                uiPresetListName = '{}.presets'.format(uiOptionMetadataName)
                if taskHolder.task().hasMetadata(uiPresetListName):
                    for preset in taskHolder.task().metadata(uiPresetListName):
                        if preset in presets:
                            continue
                        presets.append(preset)

                # editable presets
                uiEditableName = '{}.editable'.format(uiOptionMetadataName)
                if taskHolder.task().hasMetadata(uiEditableName) and taskHolder.task().metadata(uiEditableName):
                    w.setEditable(True)

                w.addItems(presets)
                signal = w.currentTextChanged
            else:
                w = QtWidgets.QLineEdit(str(value))

                regex = '{}.regex'.format(uiOptionMetadataName)
                if taskHolder.task().hasMetadata(regex):
                    w.setValidator(QtGui.QRegExpValidator(taskHolder.task().metadata(regex)))

                caseStyle = '{}.caseStyle'.format(uiOptionMetadataName)
                if taskHolder.task().hasMetadata(caseStyle):
                    def __toUpper(w, case, text):
                        w.setText(text.upper() if case == 'uppercase' else text.lower())
                    w.textEdited.connect(functools.partial(__toUpper, w, taskHolder.task().metadata(caseStyle)))

                signal = w.editingFinished

        if signal:
            signal.connect(functools.partial(self.__editOption, signalWidget or w, optionName, taskHolder, assignTo))

        return w

    def __hasUpdateInfo(self, taskHolder):
        """
        Return a boolean telling if the task held by the task holder has the update info method.
        """
        return hasattr(taskHolder.task(), 'updateInfo') and hasattr(taskHolder.task().updateInfo, '__call__')

    def __createTask(self, parentEntry, taskHolder, suffix='', mainOptions=None, path=''):
        """
        Create the task widget information.
        """
        taskName = taskHolder.task().type()

        taskChild = QtWidgets.QTreeWidgetItem(parentEntry)
        taskChild.setData(0, QtCore.Qt.EditRole, Template.runProcedure('camelcasetospaced', taskName))
        taskChild.setData(1, QtCore.Qt.EditRole, suffix)
        isRootTask = mainOptions is None
        taskChild.setExpanded(isRootTask)

        # creating the path
        path = path if not path else '{}/'.format(path)
        path += Template.runProcedure('camelcasetospaced', taskName)

        # options
        if mainOptions is None:
            mainOptions = QtWidgets.QTreeWidgetItem(taskChild)
            mainOptions.setData(0, QtCore.Qt.EditRole, 'Main')
            mainOptions.setExpanded(True)
            mainOptions.setHidden(True)

            if self.__hasUpdateInfo(taskHolder):
                infoAreaGroup = QtWidgets.QTreeWidgetItem(taskChild)
                infoAreaGroup.setData(0, QtCore.Qt.EditRole, 'Info')
                infoAreaGroup.setExpanded(True)

                infoAreaEntry = QtWidgets.QTreeWidgetItem(infoAreaGroup)
                infoAreaEntry.setData(0, QtCore.Qt.EditRole, '')
                infoWidget = QtWidgets.QTextEdit(self)
                infoWidget.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
                infoWidget.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
                infoWidget.setObjectName('infoArea')
                infoWidget.setMinimumHeight(100)
                infoWidget.setMaximumHeight(100)

                infoWidget.setReadOnly(True)

                taskChild.infoWidget = weakref.ref(infoWidget)
                self.setItemWidget(
                    infoAreaEntry,
                    1,
                    infoWidget
                )

        # only showing task advanced in under the root level once
        if isRootTask:
            advancedEntry = QtWidgets.QTreeWidgetItem(taskChild)
            advancedEntry.setData(0, QtCore.Qt.EditRole, 'Task advanced')
            advancedEntry.setExpanded(False)
        else:
            advancedEntry = taskChild

        for optionName in taskHolder.task().optionNames():
            parentEntry = advancedEntry
            optionDisplayName = Template.runProcedure('camelcasetospaced', optionName)
            uiOptionMetadataName = 'ui.options.{}'.format(optionName)

            # main option
            uiOptionMainName = '{}.main'.format(uiOptionMetadataName)
            tooltip = ""
            if taskHolder.task().hasMetadata(uiOptionMainName) and taskHolder.task().metadata(uiOptionMainName):
                parentEntry = mainOptions
                tooltip = "{}: {}".format(
                    '/'.join(path.split('/')),
                    Template.runProcedure('camelcasetospaced', optionName)
                )

            # custom label
            uiOptionLabelName = '{}.label'.format(uiOptionMetadataName)
            customLabel = taskHolder.task().metadata(uiOptionLabelName) if taskHolder.task().hasMetadata(uiOptionLabelName) else optionDisplayName

            optionEntry = QtWidgets.QTreeWidgetItem(parentEntry)
            optionEntry.setData(0, QtCore.Qt.EditRole, customLabel)

            if tooltip:
                optionEntry.setToolTip(0, tooltip)

            value = taskHolder.task().option(optionName)
            w = self.__buildOptionWidget(taskHolder, optionName, value, [], mainOptions)

            self.setItemWidget(optionEntry, 1, w)

        # advanced
        taskSetupEntry = QtWidgets.QTreeWidgetItem(advancedEntry)
        taskSetupEntry.setData(0, QtCore.Qt.EditRole, 'Setup')

        if 'contextConfig' in taskHolder.varNames():
            configName = QtWidgets.QTreeWidgetItem(taskSetupEntry)
            configName.setData(0, QtCore.Qt.EditRole, 'Config')
            configName.setData(1, QtCore.Qt.EditRole, taskHolder.var('contextConfig'))

        # status
        uiStatusMetadataName = 'ui.status'
        uiStatusMainName = '{}.main'.format(uiStatusMetadataName)
        tooltip = ''
        statusEntry = taskSetupEntry
        if taskHolder.task().hasMetadata(uiStatusMainName) and taskHolder.task().metadata(uiStatusMainName):
            statusEntry = mainOptions
            tooltip = '{}/Advanced: Status'.format(
                '/'.join(path.split('/'))
            )

        # custom status label
        uiStatusLabelName = '{}.label'.format(uiStatusMetadataName)
        customLabel = taskHolder.task().metadata(uiStatusLabelName) if taskHolder.task().hasMetadata(uiStatusLabelName) else 'Status'
        statusEntry = QtWidgets.QTreeWidgetItem(statusEntry)
        if tooltip:
            statusEntry.setToolTip(0, tooltip)

        statusEntry.setData(0, QtCore.Qt.EditRole, customLabel)
        statusWidget = QtWidgets.QComboBox()
        statusList = [
            taskHolder.status()
        ]
        for statusName in taskHolder.statusTypes:
            if statusName in statusList:
                continue

            uiStatusHideName = '{}.{}.hide'.format(uiStatusMetadataName, statusName)
            if taskHolder.task().hasMetadata(uiStatusHideName) and taskHolder.task().metadata(uiStatusHideName):
                continue

            statusList.append(statusName)

        statusWidget.addItems(statusList)
        self.setItemWidget(
            statusEntry,
            1,
            statusWidget
        )
        statusWidget.currentTextChanged.connect(functools.partial(self.__editStatus, statusWidget, taskHolder))

        # target template
        templateEntry = QtWidgets.QTreeWidgetItem(taskSetupEntry)
        templateEntry.setData(0, QtCore.Qt.EditRole, 'Target')
        templateWidget = QtWidgets.QLineEdit(taskHolder.targetTemplate().inputString())
        self.setItemWidget(
            templateEntry,
            1,
            templateWidget
        )
        templateWidget.editingFinished.connect(functools.partial(self.__editTemplate, templateWidget, 'target', taskHolder))

        # filter template
        filterTemplate = QtWidgets.QTreeWidgetItem(taskSetupEntry)
        filterTemplate.setData(0, QtCore.Qt.EditRole, 'Filter')
        templateWidget = QtWidgets.QLineEdit(taskHolder.filterTemplate().inputString())
        self.setItemWidget(
            filterTemplate,
            1,
            templateWidget
        )
        templateWidget.editingFinished.connect(functools.partial(self.__editTemplate, templateWidget, 'filter', taskHolder))

        # export
        exportEntry = QtWidgets.QTreeWidgetItem(taskSetupEntry)
        exportEntry.setData(0, QtCore.Qt.EditRole, 'Export')
        templateWidget = QtWidgets.QLineEdit(taskHolder.exportTemplate().inputString())
        self.setItemWidget(
            exportEntry,
            1,
            templateWidget
        )
        templateWidget.editingFinished.connect(functools.partial(self.__editTemplate, templateWidget, 'export', taskHolder))

        # imports
        if taskHolder.importTemplates():
            importsChild = QtWidgets.QTreeWidgetItem(taskSetupEntry)
            importsChild.setData(0, QtCore.Qt.EditRole, 'Imports')

            for importTemplate in taskHolder.importTemplates():
                child = QtWidgets.QTreeWidgetItem(importsChild)
                child.setData(1, QtCore.Qt.EditRole, importTemplate.inputString())

        self.__createSubtasks(advancedEntry, taskHolder, mainOptions, path)

        # showing main options
        if mainOptions.isHidden() and mainOptions.childCount():
            mainOptions.setHidden(False)

        return taskChild

    def __editOption(self, widget, optionName, taskHolder, assignTo, value=None, *args):
        """
        Edit a task holder option.
        """
        optionValue = taskHolder.task().option(optionName)
        if isinstance(widget, QtWidgets.QCheckBox):
            value = widget.isChecked()

        elif isinstance(widget, CheckComboBox):
            checkedIndices = widget.checkedIndices()
            value = []
            for index in checkedIndices:
                value.append(widget.allValues[index])

        elif isinstance(widget, QtWidgets.QComboBox):
            value = widget.currentText()

        elif isinstance(widget, QtWidgets.QLineEdit):
            value = widget.text()

        elif isinstance(widget, QtWidgets.QTextEdit):
            value = widget.toPlainText()

        elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
            value = widget.value()
        else:
            return

        if assignTo:
            # changing data in-place
            currentLevel = optionValue
            for assignLevel in assignTo[:-1]:
                currentLevel = currentLevel[assignLevel]
            currentLevel[assignTo[-1]] = value
            value = optionValue

        taskHolder.task().setOption(optionName, value)

        # emitting task holder option changed signal
        try:
            self.taskHolderOptionChangedSignal.emit(taskHolder)
        except Exception:
            traceback.print_exc()

    def __onTaskHolderOptionChanged(self, taskHolder):
        """
        Callback called when an option changes the task holder.
        """
        if not self.__hasUpdateInfo(taskHolder):
            return

        elements = taskHolder.entry().elementList
        infoWidget = taskHolder.entry().infoWidget()

        infoResult = taskHolder.task().updateInfo(elements)

        infoWidget.setPlainText(str(infoResult))

    def __editStatus(self, widget, taskHolder, value=None):
        """
        Edit a status.
        """
        taskHolder.setStatus(widget.currentText())

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

    def __onPickerSelectDir(self, editableWidget, *args, **kwargs):
        """
        Callback triggered when select directory button is pressed.
        """
        currentPath = editableWidget.text() if isinstance(editableWidget, QtWidgets.QLineEdit) else editableWidget.currentText()
        initialPath = currentPath if os.path.exists(currentPath) else ""

        selectedFolder = QtWidgets.QFileDialog().getExistingDirectory(
            self,
            "Select Directory",
            initialPath,
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if selectedFolder:
            if isinstance(editableWidget, QtWidgets.QLineEdit):
                editableWidget.setText(selectedFolder)
            else:
                editableWidget.setCurrentText(selectedFolder)

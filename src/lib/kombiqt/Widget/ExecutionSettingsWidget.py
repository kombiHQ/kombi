import os
import datetime
import functools
import traceback
import weakref
from ..OptionVisual import OptionVisual
from kombi.Element import Element
from kombi.Task import Task, TaskValidationError
from kombi.Template import Template
from kombi.ProcessExecution import ProcessExecution
from Qt import QtCore, QtWidgets

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

    taskHolderOptionChangedSignal = QtCore.Signal(object, str)

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
        self.__elements = []
        self.__clonedTaskHolders = []

        self.taskHolderOptionChangedSignal.connect(self.__onTaskHolderOptionChanged)

    def refresh(self, elements, taskHolders):
        """
        Update the execution settings.
        """
        self.__clonedTaskHolders = list(map(lambda x: x.clone(), taskHolders))
        self.__elements = list(elements)
        self.__refreshWidgets()

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
            return False

        output = ''
        dispatchedMessage = ''
        try:
            for taskHolder, elementsGroup in self.executionTaskHolders():
                # default label
                label = "{}/{} [{}]".format(
                    os.path.basename(taskHolder.var('configDirectory')),
                    elementsGroup[0].tag('group') if 'group' in elementsGroup[0].tagNames() else elementsGroup[0].var('name'),
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

    def __refreshWidgets(self):
        """
        Refresh all tasks/options widgets.
        """
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.clear()

        self.setHeaderItem(
            QtWidgets.QTreeWidgetItem(
                ("", "")
            )
        )

        for index, taskHolder in enumerate(self.__clonedTaskHolders):
            try:
                matchedElements = taskHolder.query(self.__elements)
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
                child = self.__createTask(self, taskHolder)
                child.taskHolderIndex = index
                child.taskHolder = taskHolder
                continue

            alreadyFailed = False
            for elementList in Element.group(matchedElements):
                nameSuffix = elementList[0].var('name')

                if 'group' in elementList[0].tagNames():
                    nameSuffix = "{} ({} total)".format(
                        elementList[0].tag('group'),
                        len(elementList)
                    )

                # checking if task has the setup method
                if hasattr(taskHolder.task(), 'setup') and \
                        hasattr(taskHolder.task().setup, '__call__'):

                    try:
                        taskHolder.task().setup(elementList)
                    except Exception as err:
                        traceback.print_exc()

                        if not alreadyFailed:
                            alreadyFailed = True
                            self.__messageBox = QtWidgets.QMessageBox(
                                self,
                                "Task '{}' setup error".format(
                                    taskHolder.task().type()
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
                    taskHolder,
                    nameSuffix
                )

                taskHolder.entry = weakref.ref(matchedChild)
                matchedChild.taskHolderIndex = index
                matchedChild.elementList = elementList
                matchedChild.taskHolder = taskHolder

                # option to enable the task holder
                matchedChild.setCheckState(0, QtCore.Qt.Checked)

                # emitting task holder option changed signal
                try:
                    self.taskHolderOptionChangedSignal.emit(taskHolder, '')
                except Exception:
                    traceback.print_exc()

        self.resizeColumnToContents(0)
        QtWidgets.QApplication.restoreOverrideCursor()

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

    def __buildOptionWidget(self, taskHolder, optionName, optionValue):
        """
        Create the option widget.
        """
        uiHints = {}
        uiOptionMetadataName = 'ui.options.{}'.format(optionName)
        if taskHolder.task().hasMetadata(uiOptionMetadataName):
            uiHints = taskHolder.task().metadata(uiOptionMetadataName)

        optionVisualWidget = OptionVisual.create(optionName, optionValue, uiHints)
        optionVisualWidget.valueChanged.connect(functools.partial(self.__onEditOption, taskHolder, optionName))

        return optionVisualWidget

    def __createTask(self, parentEntry, taskHolder, suffix='', mainOptions=None, path=''):
        """
        Create the task widget information.
        """
        taskName = taskHolder.task().type()

        taskChild = QtWidgets.QTreeWidgetItem(parentEntry)
        taskChild.setData(0, QtCore.Qt.EditRole, Template.runProcedure('camelcasetospaced', taskName) + '   ')
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

        # only showing task advanced in under the root level once
        if isRootTask:
            advancedEntry = QtWidgets.QTreeWidgetItem(taskChild)
            advancedEntry.setData(0, QtCore.Qt.EditRole, 'Advanced')
            advancedEntry.setExpanded(False)
        else:
            advancedEntry = taskChild

        for optionName in taskHolder.task().optionNames():
            uiOptionMetadataName = 'ui.options.{}'.format(optionName)

            # in case the hidden metadata is defined we don't render it
            hiddenMetadata = f'{uiOptionMetadataName}.hidden'
            if taskHolder.task().hasMetadata(hiddenMetadata) and taskHolder.task().metadata(hiddenMetadata):
                continue

            parentEntry = advancedEntry
            optionDisplayName = Template.runProcedure('camelcasetospaced', optionName)

            # main option
            uiOptionMainName = '{}.main'.format(uiOptionMetadataName)
            tooltip = ""
            if taskHolder.task().hasMetadata(uiOptionMainName) and taskHolder.task().metadata(uiOptionMainName):
                parentEntry = mainOptions
                tooltip = "{}: {}".format(
                    '/'.join(path.split('/')),
                    Template.runProcedure('camelcasetospaced', optionName)
                )

            # in case there is a separator hint
            hiddenMetadata = f'{uiOptionMetadataName}.separator'
            if taskHolder.task().hasMetadata(hiddenMetadata) and taskHolder.task().metadata(hiddenMetadata):
                separatorEntry = QtWidgets.QTreeWidgetItem(parentEntry)
                self.setItemWidget(separatorEntry, 0, _TreeItemSeparatorWidget())
                self.setItemWidget(separatorEntry, 1, _TreeItemSeparatorWidget())

            # custom label
            uiOptionLabelName = '{}.label'.format(uiOptionMetadataName)
            customLabel = taskHolder.task().metadata(uiOptionLabelName) if taskHolder.task().hasMetadata(uiOptionLabelName) else optionDisplayName

            optionEntry = QtWidgets.QTreeWidgetItem(parentEntry)
            optionEntry.setData(0, QtCore.Qt.EditRole, customLabel)
            optionEntry.setTextAlignment(0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)

            if tooltip:
                optionEntry.setToolTip(0, tooltip)

            optionValue = taskHolder.task().option(optionName)
            optionVisualWidget = self.__buildOptionWidget(taskHolder, optionName, optionValue)
            self.setItemWidget(optionEntry, 1, optionVisualWidget)

        # advanced
        taskSetupEntry = QtWidgets.QTreeWidgetItem(advancedEntry)
        taskSetupEntry.setData(0, QtCore.Qt.EditRole, 'Setup')

        if 'contextConfig' in taskHolder.varNames():
            configName = QtWidgets.QTreeWidgetItem(taskSetupEntry)
            configName.setData(0, QtCore.Qt.EditRole, 'Config')
            configName.setTextAlignment(0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
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
        statusEntry.setTextAlignment(0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
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
        templateEntry.setTextAlignment(0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
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
        filterTemplate.setTextAlignment(0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
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
        exportEntry.setTextAlignment(0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
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
            importsChild.setTextAlignment(0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)

            for importTemplate in taskHolder.importTemplates():
                child = QtWidgets.QTreeWidgetItem(importsChild)
                child.setData(1, QtCore.Qt.EditRole, importTemplate.inputString())

        self.__createSubtasks(advancedEntry, taskHolder, mainOptions, path)

        # showing main options
        if mainOptions.isHidden() and mainOptions.childCount():
            mainOptions.setHidden(False)

        return taskChild

    def __onEditOption(self, taskHolder, optionName, optionValue):
        """
        Edit a task holder option.
        """
        taskHolder.task().setOption(optionName, optionValue)

        # emitting task holder option changed signal
        try:
            self.taskHolderOptionChangedSignal.emit(taskHolder, optionName)
        except Exception:
            traceback.print_exc()

    def __onTaskHolderOptionChanged(self, taskHolder, optionName):
        """
        Callback called when an option changes the task holder.
        """
        # in case the option has the rebuild on change ui hint the whole UI will be redraw.
        if not optionName:
            return

        uiHintResetOnChange = 'ui.options.{}.rebuildOnChange'.format(optionName)
        if taskHolder.task().hasMetadata(uiHintResetOnChange) and taskHolder.task().metadata(uiHintResetOnChange):
            self.__refreshWidgets()

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

class _TreeItemSeparatorWidget(QtWidgets.QWidget):
    """
    Implements a basic separator widget.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        separatorWidget = QtWidgets.QWidget()
        separatorWidget.setObjectName('treeItemSeparator')
        separatorWidget.setFixedHeight(2)
        self.layout().addWidget(separatorWidget)

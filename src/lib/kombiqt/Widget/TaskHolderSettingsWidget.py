import os
import datetime
import functools
import traceback
from ..OptionVisual import OptionVisual
from kombi.Element import Element
from kombi.TaskHolder import TaskHolder
from kombi.Task import Task, TaskValidationError
from kombi.Template import Template
from kombi.ProcessExecution import ProcessExecution
from kombi.KombiError import KombiError
from Qt import QtCore, QtWidgets

class TaskHolderSettingsWidgetError(KombiError):
    """
    Base exception for execution settings widget error.
    """

class TaskHolderSettingsWidgetRequiredError(TaskHolderSettingsWidgetError):
    """
    Custom exception type raised when a required option is empty.
    """

    def __init__(self, message, task):
        """
        Create an execution settings widget required error object.
        """
        super(TaskHolderSettingsWidgetRequiredError, self).__init__(message)
        assert isinstance(task, Task), "Invalid task type!"

        self.__task = task

    def task(self):
        """
        Return the task associated with the error.
        """
        return self.__task

class TaskHolderSettingsWidget(QtWidgets.QTreeWidget):
    """
    This widget is used to list the tasks options.
    """

    taskHolderOptionChangedSignal = QtCore.Signal(object, list)

    def __init__(self, *args, **kwargs):
        """
        Create a TaskHolderSettingsWidget object.
        """
        super(TaskHolderSettingsWidget, self).__init__(*args, **kwargs)
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
        self.__taskHolders = []
        self.__changedOptions = {}
        self.__verticalSourceScrollBarLatestPos = 0

        self.taskHolderOptionChangedSignal.connect(self.__onTaskHolderOptionChanged)

    def refresh(self, elements, taskHolders):
        """
        Update the execution settings.
        """
        self.__taskHolders = taskHolders
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
                for task in item.taskHolder().childTasks():

                    # running validations without any elements (this will allow validations
                    # that verify for options to take affect in all tasks)
                    try:
                        task.validate()
                    except TaskValidationError as err:
                        raise TaskHolderSettingsWidgetRequiredError(
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
                                    raise TaskHolderSettingsWidgetRequiredError(
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
                                    raise TaskHolderSettingsWidgetRequiredError(
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
                                raise TaskHolderSettingsWidgetRequiredError(
                                    'Option "{}" is required (it cannot be empty)'.format(
                                        displayOptionName
                                    ),
                                    task
                                )

                # running validations
                try:
                    item.taskHolder().task().validate(item.elements())
                except TaskValidationError as err:
                    raise TaskHolderSettingsWidgetRequiredError(
                        str(err),
                        item.taskHolder().task()
                    )

                result.append((item.taskHolder(), item.elements()))

        return result

    def execute(self, dispatcher, showOutput=True, showDispatchedMessage=None):
        """
        Execute the task holders.
        """
        # by default the dispatched message is not displayed only for the runtime dispatcher. This
        # behavior can be toggled on or off using a UI hint
        if showDispatchedMessage is None:
            showDispatchedMessage = dispatcher.type() != 'runtime'
            if self.__taskHolders and 'uiHintShowDispatchedMessage' in self.__taskHolders[0].tagNames():
                showDispatchedMessage = self.__taskHolders[0].tag('uiHintShowDispatchedMessage')

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

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        output = ''
        dispatchedMessage = ''
        try:
            for taskHolder, elementsGroup in self.executionTaskHolders():
                # default label
                label = "{}/{} [{}]".format(
                    os.path.basename(taskHolder.var('configDirectory', '')) or taskHolder.task().type(),
                    elementsGroup[0].tag('group') if 'group' in elementsGroup[0].tagNames() else elementsGroup[0].tag('label'),
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

            QtWidgets.QApplication.restoreOverrideCursor()
            self.__messageBox = QtWidgets.QMessageBox(
                self,
                "Execution",
                QtWidgets.QMessageBox.Ok
            )
            self.__messageBox.setWindowModality(QtCore.Qt.NonModal)
            self.__messageBox.setIcon(QtWidgets.QMessageBox.Critical)
            self.__messageBox.setText('Failed during execution')
            self.__messageBox.setDetailedText(str(err))

            if isinstance(err, TaskHolderSettingsWidgetRequiredError):
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
            QtWidgets.QApplication.restoreOverrideCursor()
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

    def keyPressEvent(self, _):
        """
        Override keyPressEvent to prevent any key press to be interception by host apps (e.g., Maya).
        """
        pass

    def __updateRootItem(self, taskHolder):
        """
        This method is used to update the root item based on the input task holder.
        """
        self.__verticalSourceScrollBarLatestPos = self.verticalScrollBar().value()
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        for index in range(self.topLevelItemCount()):
            rootItem = self.topLevelItem(index)
            if taskHolder.task() not in rootItem.taskHolder().childTasks():
                continue

            # clearing all children
            childrenExpanded = []
            for _ in range(rootItem.childCount()):
                childrenExpanded.append(rootItem.child(0).isExpanded())
                rootItem.takeChild(0)

            # computing new children
            self.__populateTask(rootItem)

            # restoring the expanded state
            if len(childrenExpanded) == rootItem.childCount():
                for childIndex, childExpanded in enumerate(childrenExpanded):
                    rootItem.child(childIndex).setExpanded(childExpanded)
            break

        # workaround necessary to restore the position of the scrollbar
        QtCore.QTimer.singleShot(0, self.__onRestoreVerticalScrollBar)

    def __refreshWidgets(self):
        """
        Refresh all tasks/options widgets.
        """
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.clear()
        self.__changedOptions = {}

        self.setHeaderItem(
            QtWidgets.QTreeWidgetItem(
                ("", "")
            )
        )

        for taskHolder in self.__taskHolders:
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
                self.__createTask(self, taskHolder.clone())
                continue

            alreadyFailed = False
            for elementList in Element.group(matchedElements):
                nameSuffix = elementList[0].tag('label')
                clonedTaskHolder = taskHolder.clone()

                if 'group' in elementList[0].tagNames():
                    nameSuffix = "{} ({} total)".format(
                        elementList[0].tag('group'),
                        len(elementList)
                    )

                try:
                    clonedTaskHolder.task().setup(elementList)
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
                    clonedTaskHolder,
                    nameSuffix,
                    elements=elementList
                )

                # option to enable the task holder
                matchedChild.setCheckState(0, QtCore.Qt.Checked)

        for taskHolder, optionNames in self.__changedOptions.items():
            self.__onTaskHolderOptionChanged(taskHolder, optionNames)

        self.__changedOptions = {}

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

        optionVisualWidget = OptionVisual.create(optionValue, uiHints)
        # in case the value has changed during the construction lets update it directly to the task
        if optionVisualWidget.optionValue() != optionValue:
            if taskHolder not in self.__changedOptions:
                self.__changedOptions[taskHolder] = set()
            self.__changedOptions[taskHolder].add(optionName)
            taskHolder.task().setOption(optionName, optionVisualWidget.optionValue())

        optionVisualWidget.valueChanged.connect(functools.partial(self.__onEditOption, taskHolder, optionName))

        return optionVisualWidget

    def __createTask(self, parentEntry, taskHolder, suffix='', mainOptions=None, path='', elements=None):
        """
        Create the task widget information.
        """
        taskChild = TaskHolderSettingsTreeWidgetItem(parentEntry, taskHolder, elements)
        taskChild.setData(0, QtCore.Qt.EditRole, Template.runProcedure('camelcasetospaced', taskHolder.task().type()) + '   ')
        taskChild.setData(1, QtCore.Qt.EditRole, suffix)
        taskChild.setExpanded(mainOptions is None)
        self.__populateTask(taskChild, mainOptions=mainOptions, path=path)

        return taskChild

    def __populateTask(self, item, mainOptions=None, path=''):
        """
        Utility method used to populate the content for the task.
        """
        taskHolder = item.taskHolder()
        taskName = taskHolder.task().type()
        isRootTask = mainOptions is None

        # creating the path
        path = path if not path else '{}/'.format(path)
        path += Template.runProcedure('camelcasetospaced', taskName)

        # options
        if mainOptions is None:
            mainOptions = QtWidgets.QTreeWidgetItem(item)
            mainOptions.setData(0, QtCore.Qt.EditRole, 'Main')
            mainOptions.setExpanded(True)
            mainOptions.setHidden(True)

        # only showing task advanced in under the root level once
        if isRootTask:
            advancedEntry = QtWidgets.QTreeWidgetItem(item)
            advancedEntry.setData(0, QtCore.Qt.EditRole, 'Advanced')
            advancedEntry.setExpanded(False)
        else:
            advancedEntry = item

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

        self.setItemWidget(
            statusEntry,
            1,
            self.__statusWidget(taskHolder)
        )

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

        # profile
        profileEntry = QtWidgets.QTreeWidgetItem(taskSetupEntry)
        profileEntry.setData(0, QtCore.Qt.EditRole, 'Profile')
        profileEntry.setToolTip(0, 'When a path is provided, saves a PNG image about a profile for the task execution')
        profileEntry.setTextAlignment(0, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
        templateWidget = QtWidgets.QLineEdit(taskHolder.profileTemplate().inputString())
        self.setItemWidget(
            profileEntry,
            1,
            templateWidget
        )
        templateWidget.editingFinished.connect(functools.partial(self.__editTemplate, templateWidget, 'profile', taskHolder))

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

    def __onRestoreVerticalScrollBar(self):
        """
        Slot triggered to restore the vertical scrollbar position.
        """
        self.verticalScrollBar().setSliderPosition(self.__verticalSourceScrollBarLatestPos)

    def __statusWidget(self, taskHolder):
        """
        Build the status widget.
        """
        uiMainStatus = 'ui.status.main'
        # when the status is promoted as main, lets render it as checked box to keep it simple for the user
        if taskHolder.task().hasMetadata(uiMainStatus) and taskHolder.task().metadata(uiMainStatus):
            statusWidget = QtWidgets.QCheckBox()
            statusWidget.setChecked(taskHolder.status() == 'execute')
            statusWidget.stateChanged.connect(functools.partial(self.__editStatus, statusWidget, taskHolder))
        # otherwise, render all status inside of a dropdown
        else:
            statusWidget = QtWidgets.QComboBox()
            statusWidget.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

            statusWidget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
            statusList = [
                taskHolder.status()
            ]
            for statusName in taskHolder.statusTypes:
                if statusName in statusList:
                    continue

                statusList.append(statusName)

            statusWidget.addItems(statusList)
            statusWidget.currentTextChanged.connect(functools.partial(self.__editStatus, statusWidget, taskHolder))

        # we need to create a container for the combobox so it does not expand
        # to use the whole width
        statusContainerLayout = QtWidgets.QHBoxLayout()
        statusContainerLayout.setContentsMargins(0, 0, 0, 0)
        statusContainerLayout.addWidget(statusWidget)
        statusContainerLayout.addStretch()
        statusContainer = QtWidgets.QWidget()
        statusContainer.setLayout(statusContainerLayout)

        return statusContainer

    def __onEditOption(self, taskHolder, optionName, optionValue):
        """
        Edit a task holder option.
        """
        # same value no need to update
        if taskHolder.task().option(optionName) == optionValue:
            return

        taskHolder.task().setOption(optionName, optionValue)

        # emitting task holder option changed signal
        self.taskHolderOptionChangedSignal.emit(taskHolder, [optionName])

    def __onTaskHolderOptionChanged(self, taskHolder, optionNames):
        """
        Callback called when an option changes the task holder.
        """
        refreshWidgets = False
        for optionName in optionNames:
            uiHintResetOnChange = 'ui.options.{}.rebuildOnChange'.format(optionName)
            if taskHolder.task().hasMetadata(uiHintResetOnChange) and taskHolder.task().metadata(uiHintResetOnChange):
                refreshWidgets = True
                break

        if not refreshWidgets:
            return False

        try:
            self.__updateRootItem(taskHolder)
        except Exception:
            traceback.print_exc()

        return True

    def __editStatus(self, widget, taskHolder, *_args):
        """
        Edit a status.
        """
        if isinstance(widget, QtWidgets.QCheckBox):
            status = "execute" if widget.isChecked() else "ignore"
            taskHolder.setStatus(status)
        else:
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

        elif template == "profile":
            taskHolder.profileTemplate().setInputString(value)

class TaskHolderSettingsTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    """
    Custom tree widget item used to represent a task holder in the execution settings tree.
    """
    def __init__(self, parent, taskHolder, elements=None):
        """
        Create TaskHolderSettingsTreeWidgetItem object.
        """
        super().__init__(parent)
        self.__elements = []

        self.__setTaskHolder(taskHolder)
        if elements:
            self.__setElements(elements)

    def taskHolder(self):
        """
        Return the task holder associated with the tree item.
        """
        return self.__taskHolder

    def elements(self):
        """
        Return a list of elements associated with the tree item.
        """
        return self.__elements

    def __setElements(self, elements):
        """
        Set the elements associated with the tree item.
        """
        self.__elements = elements

    def __setTaskHolder(self, taskHolder):
        """
        Set the task holder associated with the tree item.
        """
        assert isinstance(taskHolder, TaskHolder), 'Invalid task holder type'
        self.__taskHolder = taskHolder

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

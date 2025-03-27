from kombi.TaskHolder import TaskHolder
from kombi.Template import Template
from kombi.Dispatcher import Dispatcher
from Qt import QtCore, QtWidgets
from .TaskHolderListWidget import TaskHolderListWidget
from ..Resource import Resource
from ..Widget.DispatcherListWidget import DispatcherListWidget

class TaskHolderExecutionSettingsWidget(QtWidgets.QWidget):
    """
    Widget used to execute task holders by showing the task holder list, dispatcher and execution button.
    """
    executionSuccess = QtCore.Signal(bool)

    def __init__(self, taskHolders, elements=None, defaultDispatcherName='runtime', parent=None):
        """
        Create TaskHolderExecutionSettingsWidget object.
        """
        super(TaskHolderExecutionSettingsWidget, self).__init__(parent)

        self.__setTaskHolders(taskHolders)
        self.__setDefaultDispatcherName(defaultDispatcherName)
        self.__mainLayout = QtWidgets.QVBoxLayout()
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.__mainLayout)

        self.__buildWidgets()
        self.refresh(elements)

    def refresh(self, elements=None):
        """
        Refresh the widget.
        """
        self.__taskHolderSettingsWidget.refresh(elements or [], self.taskHolders())

    def taskHolders(self):
        """
        Return the task holders used by the widget.
        """
        return self.__taskHolders

    def defaultDispatcherName(self):
        """
        Return the default dispatcher name.
        """
        return self.__defaultDispatcherName

    @classmethod
    def popup(cls, taskHolders, elements, defaultDispatcherName='runtime', title=None, width=800, height=600, parent=None):
        """
        Display a popup dialog to execute the task holders and elements.
        """
        runTaskHoldersWidget = cls(taskHolders, elements, defaultDispatcherName)

        dialog = _TaskHolderExecutionDialog(parent)
        dialog.resize(width, height)

        def __closeDialog(success):
            dialog.setSuccess(success)
            if success:
                dialog.close()
        runTaskHoldersWidget.executionSuccess.connect(__closeDialog)

        if title is None:
            title = 'Execute {}'.format(
                Template.runProcedure('camelcasetospaced', taskHolders[0].task().metadata('name'))
            )

        dialog.setWindowTitle(title)
        dialog.setStyleSheet(Resource.stylesheet())
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(runTaskHoldersWidget)
        dialog.setLayout(layout)
        dialog.exec_()

        return dialog.result

    @classmethod
    def run(cls, taskHolders, elements, defaultDispatcherName='runtime', parent=None):
        """
        Perform the task holders with the input elements.

        In case the metadata showTaskHolderList is defined to False. The
        execution will be headless.
        """
        showTaskHolderList = True
        if taskHolders[0].task().hasMetadata('ui.task.showTaskHolderList'):
            showTaskHolderList = taskHolders[0].task().metadata('ui.task.showTaskHolderList')

        if showTaskHolderList:
            return cls.popup(taskHolders, elements, defaultDispatcherName, parent=parent)
        else:
            return cls(taskHolders, elements, defaultDispatcherName).performTaskHolderList()

    def __buildWidgets(self):
        """
        Build the base widgets.
        """
        self.__taskHolderSettingsWidget = TaskHolderListWidget()
        taskHolder = self.taskHolders()[0]
        self.__selectedDispatcher = DispatcherListWidget()
        self.__selectedDispatcher.selectDispatcher(self.defaultDispatcherName())
        if 'uiHintDispatcher' in taskHolder.tagNames():
            self.__selectedDispatcher.selectDispatcher(taskHolder.tag('uiHintDispatcher'))

        self.__mainLayout.addWidget(self.__taskHolderSettingsWidget)

        runButton = QtWidgets.QPushButton('Execute')
        if 'uiHintExecuteButtonLabel' in taskHolder.tagNames():
            runButton.setText(taskHolder.tag('uiHintExecuteButtonLabel'))

        runButton.setFocusPolicy(QtCore.Qt.NoFocus)
        runButton.setToolTip('Performs the task')

        runLayout = QtWidgets.QHBoxLayout()
        runLayout.addWidget(self.__selectedDispatcher)
        runLayout.addStretch()
        runLayout.addWidget(runButton)
        self.__mainLayout.addLayout(runLayout)

        runButton.clicked.connect(self.performTaskHolderList)

    def performTaskHolderList(self):
        """
        Run the task holders.
        """
        dispatcher = Dispatcher.create(self.__selectedDispatcher.selectedDispatcher())
        success = self.__taskHolderSettingsWidget.execute(dispatcher, showOutput=False)

        self.executionSuccess.emit(success)

        return success

    def __setDefaultDispatcherName(self, defaultDispatcherName):
        """
        Set the default dispatcher that should be used by the UI.
        """
        self.__defaultDispatcherName = defaultDispatcherName

    def __setTaskHolders(self, taskHolders):
        """
        Set the task holders used by the widget.
        """
        assert isinstance(taskHolders, (tuple, list)), 'Invalid list of task holders'

        for taskHolder in taskHolders:
            assert isinstance(taskHolder, TaskHolder), 'Invalid task holder type'

        self.__taskHolders = taskHolders

class _TaskHolderExecutionDialog(QtWidgets.QDialog):
    """
    Custom Dialog used to run the task holders.
    """

    def __init__(self, parent=None):
        """
        Create _TaskHolderExecutionDialog object.
        """
        super().__init__(parent)
        self.setSuccess(False)

    def setSuccess(self, value):
        """
        Set the execution success.
        """
        self.__sucess = value

    def success(self):
        """
        Return the execution success.
        """
        return self.__sucess

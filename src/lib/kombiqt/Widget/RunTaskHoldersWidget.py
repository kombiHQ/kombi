from .ExecutionSettingsWidget import ExecutionSettingsWidget
from kombi.TaskHolder import TaskHolder
from kombi.Template import Template
from kombi.Dispatcher import Dispatcher
from Qt import QtCore, QtWidgets
from ..Resource import Resource
from ..Widget.DispatcherListWidget import DispatcherListWidget

class RunTaskHoldersWidget(QtWidgets.QWidget):
    """
    This widget is used to list the tasks options.
    """
    executionSuccess = QtCore.Signal(bool)

    def __init__(self, taskHolders, elements=None, defaultDispatcherName='runtime', parent=None):
        """
        Create RunTaskHoldersWidget object.
        """
        super(RunTaskHoldersWidget, self).__init__(parent)

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
        self.__executionSettingsWidget.refresh(elements or [], self.taskHolders())

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

        dialog = QtWidgets.QDialog(parent)
        dialog.resize(width, height)
        dialog.result = False

        def __closeDialog(success):
            dialog.result = success
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

        In case the metadata showExecutionSettings is defined to False. The
        execution will be headless.
        """
        showExecutionSettings = True
        if taskHolders[0].task().hasMetadata('ui.task.showExecutionSettings'):
            showExecutionSettings = taskHolders[0].task().metadata('ui.task.showExecutionSettings')

        if showExecutionSettings:
            return cls.popup(taskHolders, elements, defaultDispatcherName, parent=parent)
        else:
            return cls(taskHolders, elements, defaultDispatcherName).performExecutionSettings()

    def __buildWidgets(self):
        """
        Build the base widgets.
        """
        self.__executionSettingsWidget = ExecutionSettingsWidget()
        taskHolder = self.taskHolders()[0]
        self.__selectedDispatcher = DispatcherListWidget()
        self.__selectedDispatcher.selectDispatcher(self.defaultDispatcherName())
        if '__uiHintDispatcher' in taskHolder.tagNames():
            self.__selectedDispatcher.selectDispatcher(taskHolder.tag('__uiHintDispatcher'))

        self.__mainLayout.addWidget(self.__executionSettingsWidget)

        runButton = QtWidgets.QPushButton('Execute')
        if '__uiHintExecuteButtonLabel' in taskHolder.tagNames():
            runButton.setText(taskHolder.tag('__uiHintExecuteButtonLabel'))

        runButton.setFocusPolicy(QtCore.Qt.NoFocus)
        runButton.setToolTip('Performs the task')

        runLayout = QtWidgets.QHBoxLayout()
        runLayout.addWidget(self.__selectedDispatcher)
        runLayout.addStretch()
        runLayout.addWidget(runButton)
        self.__mainLayout.addLayout(runLayout)

        runButton.clicked.connect(self.performExecutionSettings)

    def performExecutionSettings(self):
        """
        Run the task holders.
        """
        dispatcher = Dispatcher.create(self.__selectedDispatcher.selectedDispatcher())
        success = self.__executionSettingsWidget.execute(dispatcher, showOutput=False)

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

import functools
from Qt import QtWidgets, QtCore
from kombi.Template import Template
from kombi.TaskHolder import TaskHolder
from ..Resource import Resource
from ..Widget.RunTaskHoldersWidget import RunTaskHoldersWidget

class TasksMenu(QtWidgets.QMenu):
    """
    Utility menu that computes the tasks as entries based on the tasks holders and elements.
    """
    executed = QtCore.Signal()

    def __init__(self, taskHolders, parent=None):
        """
        Create a TaskMenu object.
        """
        super().__init__(parent)
        self.__setTaskHolders(taskHolders)

    def taskHolders(self):
        """
        Return a list of task holders associated with this menu.
        """
        return self.__taskHolders

    def addElements(self, elements):
        """
        Compute the entries based on the input elements and the task holders used to create the menu.
        """
        subMenus = {}
        for index, taskHolder in enumerate(self.__taskHolders):
            filteredElements = []
            for element in elements:
                if not taskHolder.matcher().match(element):
                    continue
                filteredElements.append(element)

            if not filteredElements or not taskHolder.task().metadata('ui.task.showInContextMenu', True):
                continue

            taskName = Template.runProcedure('camelcasetospaced', taskHolder.task().metadata('name'))
            if taskHolder.task().metadata('ui.task.showExecutionSettings', True):
                taskName += ' ...'

            currentMenu = self
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
            if taskHolder.task().metadata('ui.task.menuSeparator', False):
                currentMenu.addSeparator()

            actionArgs = []
            # in case there is an icon defined by the "ui.task.menuIcon" metadata
            if taskHolder.task().hasMetadata('ui.task.menuIcon'):
                actionArgs.append(Resource.icon(taskHolder.task().metadata('ui.task.menuIcon')))
            actionArgs.append(taskName)
            action = currentMenu.addAction(*actionArgs)
            action.triggered.connect(functools.partial(self.__onRunTaskHolder, index, filteredElements))

    def __setTaskHolders(self, taskHolders):
        """
        Associate a list of task holders to the menu.
        """
        assert isinstance(taskHolders, (list, tuple)), 'Invalid task holders list!'

        # validate task holders
        for taskHolder in taskHolders:
            assert isinstance(taskHolder, TaskHolder), 'Invalid task holder type!'

        self.__taskHolders = taskHolders

    def __onRunTaskHolder(self, index, elements):
        """
        Slog triggered by the context menu action to run the task holders.
        """
        # we want to centralize the task holders widget based on the parent widget,
        # if available, rather than the menu itself. This ensures the window is
        # positioned relative to the parent rather than the menu when a parent 
        # widget exists
        parent = self.parent() if self.parent() else self
        if RunTaskHoldersWidget.run([self.__taskHolders[index]], elements, parent=parent):
            self.executed.emit()

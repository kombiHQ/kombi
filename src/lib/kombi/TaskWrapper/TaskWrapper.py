from ..Task import Task

class TaskWrapperError(Exception):
    """Task wrapper error."""

class TaskWrapperTypeNotFoundError(TaskWrapperError):
    """Task wrapper type not found error."""

class TaskWrapperInvalidOptionError(TaskWrapperError):
    """Task wrapper invalid option error."""

class TaskWrapper(object):
    """
    Default Task wrapper.

    A task wrapper can be used to perform a task inside of a special container.
    """

    __registered = {}

    def __init__(self, taskWrapperType):
        """
        Create a task object.
        """
        self.__options = {}
        self.__taskWrapperType = taskWrapperType

    def type(self):
        """
        Return the task wrapper type.
        """
        return self.__taskWrapperType

    def option(self, name):
        """
        Return a value for an option.
        """
        if name not in self.__options:
            raise TaskWrapperInvalidOptionError(
                'Invalid option name: "{0}"'.format(
                    name
                )
            )

        return self.__options[name]

    def setOption(self, name, value):
        """
        Set an option to the task.
        """
        self.__options[name] = value

    def optionNames(self):
        """
        Return a list of the option names.
        """
        return list(self.__options.keys())

    def run(self, task):
        """
        Run the task wrapper.
        """
        assert isinstance(task, Task), "Invalid task type!"

        return self._perform(task)

    def _perform(self, task):
        """
        Execute the task.

        For re-implementation: should implement the execution of the task.
        """
        # executing task
        return task.output()

    @staticmethod
    def register(name, taskClass):
        """
        Register a task wrapper type.
        """
        assert issubclass(taskClass, TaskWrapper), \
            "Invalid task wrapper class!"

        TaskWrapper.__registered[name] = taskClass

    @staticmethod
    def registeredNames():
        """
        Return a list of registered task wrappers.
        """
        return list(TaskWrapper.__registered.keys())

    @staticmethod
    def create(taskType, *args, **kwargs):
        """
        Create a task wrapper object.
        """
        if taskType not in TaskWrapper.__registered:
            raise TaskWrapperTypeNotFoundError(
                'Task wrapper name is not registered: "{0}"'.format(
                    taskType
                )
            )

        return TaskWrapper.__registered[taskType](taskType, *args, **kwargs)


# always providing a default implementation to wrap the task execution
TaskWrapper.register(
    'default',
    TaskWrapper
)

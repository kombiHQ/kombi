import sys
import time
from ..InfoCrate import InfoCrate

class TaskReporter(object):
    """
    Task report is used to handle the display of task output.
    """

    __registered = {}

    def __init__(self, taskName):
        """
        Create a task reporter object.
        """
        self.__setTaskName(taskName)
        self.__startTime = time.time()
        self.__endTime = None
        self.__infoCrates = []

    def startTime(self):
        """
        Return the start time.
        """
        return self.__startTime

    def endTime(self):
        """
        Return the end time.
        """
        if self.__endTime is None:
            self.__endTime = time.time()

        return self.__endTime

    def totalTime(self):
        """
        Return the total time of the execution.
        """
        return self.endTime() - self.startTime()

    def taskName(self):
        """
        Return the task name associated with the reporter.
        """
        return self.__taskName

    def addInfoCrate(self, infoCrate):
        """
        Add a infoCrate to the reporter.
        """
        assert isinstance(infoCrate, InfoCrate), "Invalid infoCrate type!"

        # resetting end time
        self.__endTime = None
        self.__infoCrates.append(infoCrate)

    def infoCrates(self):
        """
        Return a list of infoCrates associated with the report.
        """
        return self.__infoCrates

    def display(self, stream=sys.stdout):
        """
        For reimplementation: compute the result (display) of the reporter.
        """
        raise NotImplementedError

    @classmethod
    def register(cls, name, reporter):
        """
        Register a reporter.
        """
        assert issubclass(reporter, TaskReporter), \
            "Invalid reporter class!"

        cls.__registered[name] = reporter

    @classmethod
    def registeredNames(cls):
        """
        Return a list of registered reporter names.
        """
        return list(cls.__registered.keys())

    @classmethod
    def create(cls, reporterName, taskName):
        """
        Create a reporter.
        """
        return cls.__registered[reporterName](taskName)

    def __setTaskName(self, name):
        """
        Set the name of the task to the reporter.
        """
        self.__taskName = name

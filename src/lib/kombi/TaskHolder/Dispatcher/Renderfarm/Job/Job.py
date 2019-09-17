from ....TaskHolder import TaskHolder
from ...Dispatcher import DispatcherError

class JobIdError(DispatcherError):
    """Render farm Job Id Error."""

class Job(object):
    """
    Abstracted render farm job class.
    """

    def __init__(self, taskHolder, jobDirectory):
        """
        Create a RenderFarmJob object.
        """
        self.__setJobDirectory(jobDirectory)
        self.__setTaskHolder(taskHolder)
        self.__dependencyIds = []
        self.__jobId = None

    def taskHolder(self):
        """
        Return the task holder associated with the render farm job.
        """
        return self.__taskHolder

    def setJobId(self, jobId):
        """
        Associate a submitted job id with the renderfarm job.
        """
        self.__jobId = jobId

    def jobId(self):
        """
        Return the job id associated with the job.

        Obviously this information is only available after the renderfarm job has been
        submitted to the farm.
        """
        if self.__jobId is None:
            raise JobIdError(
                "Renderfarm job does not have any job id associated with it."
            )

        return self.__jobId

    def addDependencyId(self, dependencyId):
        """
        Associate a dependency id with the job.
        """
        self.__dependencyIds.append(dependencyId)

    def dependencyIds(self):
        """
        Return a list of dependency ids associated with the job.
        """
        return list(self.__dependencyIds)

    def jobDirectory(self):
        """
        Return the job directory path.
        """
        return self.__jobDirectory

    def __setJobDirectory(self, jobDirectory):
        """
        Set the job directory path used temporary files about the job.
        """
        self.__jobDirectory = jobDirectory

    def __setTaskHolder(self, taskHolder):
        """
        Set the task holder object associated with render farm job.
        """
        assert isinstance(taskHolder, TaskHolder), \
            "Invalid TaskHolder type!"

        self.__taskHolder = taskHolder

from .RenderfarmJob import RenderfarmJob
from .ExpandedJob import ExpandedJob

class CollapsedJob(RenderfarmJob):
    """
    Implements a collapsed render farm job.

    A collapsed render farm job is used to await for the completion of expanded jobs.
    Then spawn a job with the result of the expanded jobs.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a render farm collapsed job object.
        """
        super(CollapsedJob, self).__init__(*args, **kwargs)

        self.__expandedJobs = []

    def addExpandedJob(self, expandedJob):
        """
        Add an expanded job that is later used as input when the collapsed job is expanded.
        """
        assert isinstance(expandedJob, ExpandedJob), \
            "Invalid ExpandedJob type!"

        self.__expandedJobs.append(expandedJob)

    def expandedJobs(self):
        """
        Return the list of expanded jobs.
        """
        return self.__expandedJobs

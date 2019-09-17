import os
import uuid
from .Job import Job

class ExpandedJob(Job):
    """
    Implements an expanded render farm job.

    An expanded job is used to run a task on the farm. The processing
    of the task can be divided by chunks or in case a task cannot
    be divided then it performs the execution of an entire task.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a render farm expanded job object.
        """
        super(ExpandedJob, self).__init__(*args, **kwargs)

        self.__chunkSize = 0
        self.__currentChunk = 0
        self.__chunkTotal = 0
        self.__totalInChunk = 0
        self.__taskResultFilePath = None

    def taskResultFilePath(self):
        """
        Return the file path about where the result of the task is going to be serialized.
        """
        if self.__taskResultFilePath is None:
            self.__taskResultFilePath = os.path.join(
                self.jobDirectory(),
                "result_{}.json".format(
                    str(uuid.uuid4())
                )
            )

        return self.__taskResultFilePath

    def setChunkSize(self, chunkSize):
        """
        Associate the chunk size with the job.
        """
        self.__chunkSize = chunkSize

    def chunkSize(self):
        """
        Return the job chunk size.
        """
        return self.__chunkSize

    def setTotalInChunk(self, totalInChunk):
        """
        Associate the information about the total crawlers in the current chunk.
        """
        self.__totalInChunk = totalInChunk

    def totalInChunk(self):
        """
        Return the information about the total of crawlers in the current chunk.
        """
        return self.__totalInChunk

    def setCurrentChunk(self, currentChunk):
        """
        Associate the information about the current chunk with the job.
        """
        self.__currentChunk = currentChunk

    def currentChunk(self):
        """
        Return information about the current chunk.
        """
        return self.__currentChunk

    def setChunkTotal(self, chunkTotal):
        """
        Associate the total number of chunks with the job.
        """
        self.__chunkTotal = chunkTotal

    def chunkTotal(self):
        """
        Return the job chunk total.
        """
        return self.__chunkTotal

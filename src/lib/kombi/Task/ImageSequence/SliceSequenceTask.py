from ...Task import Task
from ...Crawler import Crawler

class SliceSequenceTask(Task):
    """
    Implements a task that slices the image sequence crawlers.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a slice sequence task.
        """
        super(SliceSequenceTask, self).__init__(*args, **kwargs)

        self.setOption('sliceTotalAtBegin', 0)
        self.setOption('sliceTotalAtEnd', 0)

    def _perform(self):
        """
        Implement the execution of the task.
        """
        result = []

        for crawlerGroup in Crawler.group(self.crawlers()):
            sliceBegin = int(self.templateOption('sliceTotalAtBegin', crawlerGroup[0]))
            sliceEnd = int(self.templateOption('sliceTotalAtEnd', crawlerGroup[-1]))

            slicedCrawlers = crawlerGroup[sliceBegin:]
            if sliceEnd:
                slicedCrawlers = slicedCrawlers[:-sliceEnd]
            result += slicedCrawlers

        return result


# registering task
Task.register(
    'sliceSequence',
    SliceSequenceTask
)

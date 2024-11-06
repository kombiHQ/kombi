from ...Task import Task
from ...Crawler import Crawler

class RenumberSequenceTask(Task):
    """
    Implements a task that renumbers the frame variable in image sequence crawlers.

    This task returns a new crawler with the renumbered frame assigned to
    the "frame" variable (it can be changed through the option renumberedFrameVarName).
    The original frame is assigned to "originalFrame" variable (it can be changed through
    the option originalFrameVarName).
    """

    __startAtDefault = 1001

    def __init__(self, *args, **kwargs):
        """
        Create a renumber sequence task.
        """
        super(RenumberSequenceTask, self).__init__(*args, **kwargs)
        self.setOption('startAt', self.__startAtDefault)
        self.setOption('originalFrameVarName', 'originalFrame')
        self.setOption('renumberedFrameVarName', 'frame')

    def _perform(self):
        """
        Implement the execution of the task.
        """
        result = []

        for crawlerGroup in Crawler.group(self.crawlers()):
            for index, crawler in enumerate(crawlerGroup):
                newFrame = self.option('startAt') + index

                # cloning the crawler before modifying it
                newCrawler = crawler.clone()

                # setting original frame as crawler variable
                newCrawler.setVar(self.option('originalFrameVarName'), crawler.var('frame'))
                newCrawler.setVar(self.option('renumberedFrameVarName'), newFrame)
                result.append(newCrawler)

        return result


# registering task
Task.register(
    'renumberSequence',
    RenumberSequenceTask
)

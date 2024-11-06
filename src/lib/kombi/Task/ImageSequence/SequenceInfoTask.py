from ...Task import Task
from ...Crawler import Crawler

class SequenceInfoTask(Task):
    """
    Task used to assign crawler variables about the sequence first, last and total frames.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a sequence info task object.
        """
        super(SequenceInfoTask, self).__init__(*args, **kwargs)

        self.setOption('firstName', 'first')
        self.setOption('lastName', 'last')
        self.setOption('totalName', 'total')

    def _perform(self):
        """
        Implement the execution of the task.
        """
        result = []

        for crawlerGroup in Crawler.group(self.crawlers()):
            firstCrawler = crawlerGroup[0]
            lastCrawler = crawlerGroup[-1]

            for crawler in crawlerGroup:
                newCrawler = crawler.clone()
                newCrawler.setVar(
                    self.templateOption('firstName', crawler),
                    firstCrawler.var('frame')
                )
                newCrawler.setVar(
                    self.templateOption('lastName', crawler),
                    lastCrawler.var('frame')
                )
                newCrawler.setVar(
                    self.templateOption('totalName', crawler),
                    len(crawlerGroup)
                )
                result.append(newCrawler)

        return result


# registering task
Task.register(
    'sequenceInfo',
    SequenceInfoTask
)

import sys
from .TaskReporter import TaskReporter

class Columns(TaskReporter):
    """
    Implements columns task reporter.
    """

    def display(self):
        """
        Implement the column display.
        """
        # computing the crawler type column size
        crawlerTypeSize = 0
        for crawler in self.crawlers():
            crawlerTypeSize = max(len(crawler.var('type')) + 1, crawlerTypeSize)

        # printing columns
        for crawler in self.crawlers():
            sys.stdout.write(
                '{} {}{}{}\n'.format(
                    self.taskName(),
                    crawler.var('type'),
                    " " * (crawlerTypeSize - len(crawler.var('type'))),
                    crawler.var('fullPath')
                )
            )


# registering reporter
TaskReporter.register(
    'columns',
    Columns
)

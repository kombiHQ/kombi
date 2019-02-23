import sys
from .TaskReporter import TaskReporter

class Columns(TaskReporter):
    """
    Implements a columns task reporter.
    """

    def display(self):
        """
        Implement the detailed display.
        """
        for crawler in self.crawlers():
            sys.stdout.write(
                '{} {} {}\n'.format(
                    self.taskName(),
                    crawler.var('type'),
                    crawler.var('fullPath')
                )
            )


# registering reporter
TaskReporter.register(
    'columns',
    Columns
)

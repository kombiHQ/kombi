import sys
from .TaskReporter import TaskReporter

class Detailed(TaskReporter):
    """
    Implements a detailed task reporter.
    """

    def display(self):
        """
        Implement the detailed display.
        """
        sys.stdout.write(
            '{} output (execution {} seconds):\n'.format(
                self.taskName(),
                int(self.totalTime())
            )
        )

        for crawler in self.crawlers():
            sys.stdout.write(
                '  - {}\n'.format(
                    crawler
                )
            )

        sys.stdout.write('done\n')


# registering reporter
TaskReporter.register(
    'detailed',
    Detailed
)

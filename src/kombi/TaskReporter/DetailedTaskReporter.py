import sys
from .TaskReporter import TaskReporter

class DetailedTaskReporter(TaskReporter):
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

        for element in self.elements():
            sys.stdout.write(
                '  - {}\n'.format(
                    element
                )
            )

        sys.stdout.write('done\n')


# registering reporter
TaskReporter.register(
    'detailed',
    DetailedTaskReporter
)

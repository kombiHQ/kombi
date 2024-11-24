import sys
import json
from .TaskReporter import TaskReporter

class JsonTaskReporter(TaskReporter):
    """
    Implements a json task reporter.
    """

    def display(self):
        """
        Implement the json display.
        """
        result = {
            'task': self.taskName(),
            'execution': int(self.totalTime()),
            'infoCrates': []
        }

        for infoCrate in self.infoCrates():
            result['infoCrates'].append(
                {
                    'infoCrateType': infoCrate.var('type'),
                    'fullPath': infoCrate.var('fullPath')
                }
            )

        sys.stdout.write(
            '{}\n'.format(
                json.dumps(
                    result,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': ')
                )
            )
        )


# registering reporter
TaskReporter.register(
    'json',
    JsonTaskReporter
)

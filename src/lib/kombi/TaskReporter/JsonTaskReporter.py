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
            'crawlers': []
        }

        for crawler in self.crawlers():
            result['crawlers'].append(
                {
                    'crawlerType': crawler.var('type'),
                    'fullPath': crawler.var('fullPath')
                }
            )

        sys.stdout.write('{}\n'.format(
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

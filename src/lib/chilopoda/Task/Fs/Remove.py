import os
from ..Task import Task

class Remove(Task):
    """
    Remove target files task.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Remove task.
        """
        super(Remove, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        for crawler in self.crawlers():
            filePath = self.target(crawler)

            os.remove(filePath)

        # default result based on the target filePath
        return super(Remove, self)._perform()


# registering task
Task.register(
    'remove',
    Remove
)

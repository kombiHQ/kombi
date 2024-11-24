import os
from ..Task import Task

class RemoveTask(Task):
    """
    Remove target files task.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Remove task.
        """
        super(RemoveTask, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        for infoCrate in self.infoCrates():
            filePath = self.target(infoCrate)

            os.remove(filePath)

        # default result based on the target filePath
        return super(RemoveTask, self)._perform()


# registering task
Task.register(
    'remove',
    RemoveTask
)

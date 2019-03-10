import os
import shutil
from ..Task import Task, TaskError

class CopyTargetDirectoryError(TaskError):
    """Copy Target Directory Error."""

class Copy(Task):
    """
    Copies a file to the filePath.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Copy task.
        """
        super(Copy, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)
        self.setMetadata('dispatch.splitSize', 20)

    def _perform(self):
        """
        Perform the task.
        """
        for crawler in self.crawlers():
            filePath = self.target(crawler)

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(filePath))
            except OSError:
                pass

            # copying the file to the new target
            sourceFilePath = crawler.var('filePath')
            targetFilePath = filePath

            # Check if the target path already exists, if it is file remove it else raise an exception
            if os.path.isfile(targetFilePath):
                os.remove(targetFilePath)
            elif os.path.isdir(targetFilePath):
                raise CopyTargetDirectoryError(
                    'Target directory already exists {}'.format(targetFilePath)
                )

            # doing the copy
            shutil.copy2(
                sourceFilePath,
                targetFilePath
            )

        # default result based on the target filePath
        return super(Copy, self)._perform()


# registering task
Task.register(
    'copy',
    Copy
)

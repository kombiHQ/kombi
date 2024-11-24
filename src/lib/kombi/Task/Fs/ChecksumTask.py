import hashlib
from ..Task import Task, TaskError

class ChecksumTaskMatchError(TaskError):
    """Checksum match error."""

class ChecksumTask(Task):
    """
    Make sure the filePath has the same checksum as the infoCrate file path.

    In case the checksum does not match an exception is raised.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a ChecksumTask task.
        """
        super(ChecksumTask, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        for infoCrate in self.infoCrates():

            # copying the file to the new target
            sourceFilePath = infoCrate.var('filePath')
            targetFilePath = self.target(infoCrate)

            # TODO: change md5 for xxHash
            with open(sourceFilePath, 'rb') as sourceFile:
                sourceFileHash = hashlib.md5(sourceFile.read()).hexdigest()
            with open(targetFilePath, 'rb') as targetFile:
                targetFileHash = hashlib.md5(targetFile.read()).hexdigest()

            if sourceFileHash != targetFileHash:
                raise ChecksumTaskMatchError(
                    'Checksum "{0}" does not match in the target "{1}"'.format(
                        sourceFileHash,
                        targetFileHash
                    )
                )

        # default result based on the target filePath
        return super(ChecksumTask, self)._perform()


# registering task
Task.register(
    'checksum',
    ChecksumTask
)

import hashlib
from ..Task import Task, TaskError

class ChecksumMatchError(TaskError):
    """Checksum match error."""

class Checksum(Task):
    """
    Make sure the filePath has the same checksum as the crawler file path.

    In case the checksum does not match an exception is raised.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Checksum task.
        """
        super(Checksum, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        for crawler in self.crawlers():

            # copying the file to the new target
            sourceFilePath = crawler.var('filePath')
            targetFilePath = self.target(crawler)

            # TODO: change md5 for xxHash
            with open(sourceFilePath, 'rb') as sourceFile:
                sourceFileHash = hashlib.md5(sourceFile.read()).hexdigest()
            with open(targetFilePath, 'rb') as targetFile:
                targetFileHash = hashlib.md5(targetFile.read()).hexdigest()

            if sourceFileHash != targetFileHash:
                raise ChecksumMatchError(
                    'Checksum "{0}" does not match in the target "{1}"'.format(
                        sourceFileHash,
                        targetFileHash
                    )
                )

        # default result based on the target filePath
        return super(Checksum, self)._perform()


# registering task
Task.register(
    'checksum',
    Checksum
)

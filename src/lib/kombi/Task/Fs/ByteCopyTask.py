import os
import uuid
import shutil
from ...Element.Fs.FsElement import FsElement
from ..Task import Task

class ByteCopyTask(Task):
    """
    Implements a byte copy (without copying the file attributes).
    """

    def __init__(self, *args, **kwargs):
        """
        Create a byte copy object.
        """
        super(ByteCopyTask, self).__init__(*args, **kwargs)

        self.setMetadata('dispatch.split', True)
        self.setMetadata('dispatch.splitSize', 10)

    def _perform(self):
        """
        Implement the execution of the task.
        """
        result = []
        elements = self.elements()

        for element in elements:
            sourceFilePath = element.var('filePath')
            targetFilePath = self.target(element)

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            # in case the source and target are the same we are going to run the copy
            # with a temporary name for the target then later rename it to the
            # original file. Therefore, replacing the source with exactly the same file
            # but different owner/umask (this happens when running tasks through
            # a task wrapper under a different user)
            temporaryTargetName = ""
            if os.path.normpath(sourceFilePath) == os.path.normpath(targetFilePath):
                temporaryTargetName = "{}.{}".format(
                    targetFilePath,
                    uuid.uuid4()
                )

            try:
                shutil.copyfile(
                    sourceFilePath,
                    temporaryTargetName or targetFilePath
                )

                if temporaryTargetName:
                    os.rename(temporaryTargetName, targetFilePath)
            except Exception as err:
                raise err
            # removing temporary file regardless
            finally:
                if temporaryTargetName and os.path.exists(temporaryTargetName):
                    os.remove(temporaryTargetName)

            # creating a new element
            result.append(
                FsElement.createFromPath(targetFilePath)
            )

        return result


# registering task
Task.register(
    'byteCopy',
    ByteCopyTask
)

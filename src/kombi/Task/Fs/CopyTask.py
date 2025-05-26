import os
import shutil
from ..Task import Task, TaskError
from ...Element.Fs import FsElement

class CopyTaskTargetDirectoryError(TaskError):
    """Copy Target Directory Error."""

class CopyTask(Task):
    """
    Copies a file to the filePath.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a CopyTask task.
        """
        super(CopyTask, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)
        self.setMetadata('dispatch.splitSize', 20)

        # options that allow to copy vars/tags based on:
        # source var name as key to target var name as value
        self.setOption('copyVar', {})
        self.setOption('copyContextVar', {})
        self.setOption('copyTag', {})

    def _processElement(self, element):
        """
        Process an individual element.
        """
        filePath = self.target(element)

        # trying to create the directory automatically in case it does not exist
        try:
            os.makedirs(os.path.dirname(filePath))
        except OSError:
            pass

        # copying the file to the new target
        sourceFilePath = element.var('filePath')
        targetFilePath = filePath
        if os.path.normpath(sourceFilePath) == os.path.normpath(targetFilePath):
            return

        # Check if the target path already exists, if it is file remove it else raise an exception
        if os.path.isfile(targetFilePath):
            os.remove(targetFilePath)
        elif os.path.isdir(targetFilePath):
            raise CopyTaskTargetDirectoryError(
                'Target directory already exists {}'.format(targetFilePath)
            )

        # doing the copy
        if os.path.isdir(sourceFilePath):
            shutil.copytree(sourceFilePath, targetFilePath)
        else:
            shutil.copy2(sourceFilePath, targetFilePath)

        # creating result element
        newElement = FsElement.createFromPath(targetFilePath)

        # copying vars
        for sourceVarName, targetVarName in self.option('copyVar').items():
            newElement.setVar(targetVarName, element.var(sourceVarName))

        # copying context vars
        for sourceVarName, targetVarName in self.option('copyContextVar').items():
            newElement.setVar(targetVarName, element.var(sourceVarName), True)

        # copying tags
        for sourceTagName, targetTagName in self.option('copyTag').items():
            newElement.setTag(targetTagName, element.tag(sourceTagName))

        return newElement


# registering task
Task.register(
    'copy',
    CopyTask
)

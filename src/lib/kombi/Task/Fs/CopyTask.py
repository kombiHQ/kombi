import os
import shutil
from ..Task import Task, TaskError
from ...InfoCrate.Fs import FsInfoCrate

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

    def _perform(self):
        """
        Perform the task.
        """
        result = []
        for infoCrate in self.infoCrates():
            filePath = self.target(infoCrate)

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(filePath))
            except OSError:
                pass

            # copying the file to the new target
            sourceFilePath = infoCrate.var('filePath')
            targetFilePath = filePath
            if os.path.normpath(sourceFilePath) == os.path.normpath(targetFilePath):
                continue

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

            # creating result infoCrate
            newInfoCrate = FsInfoCrate.createFromPath(targetFilePath)

            # copying vars
            for sourceVarName, targetVarName in self.templateOption('copyVar', infoCrate).items():
                newInfoCrate.setVar(targetVarName, infoCrate.var(sourceVarName))

            # copying context vars
            for sourceVarName, targetVarName in self.templateOption('copyContextVar', infoCrate).items():
                newInfoCrate.setVar(targetVarName, infoCrate.var(sourceVarName), True)

            # copying tags
            for sourceTagName, targetTagName in self.templateOption('copyTag', infoCrate).items():
                newInfoCrate.setTag(targetTagName, infoCrate.tag(sourceTagName))

            result.append(newInfoCrate)

        return result


# registering task
Task.register(
    'copy',
    CopyTask
)

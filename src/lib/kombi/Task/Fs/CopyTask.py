import os
import shutil
from ..Task import Task, TaskError
from ...Crawler.Fs import FsCrawler

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
            shutil.copy2(sourceFilePath, targetFilePath)

            # creating result crawler
            newCrawler = FsCrawler.createFromPath(targetFilePath)

            # copying vars
            for sourceVarName, targetVarName in self.templateOption('copyVar', crawler).items():
                newCrawler.setVar(targetVarName, crawler.var(sourceVarName))

            # copying context vars
            for sourceVarName, targetVarName in self.templateOption('copyContextVar', crawler).items():
                newCrawler.setVar(targetVarName, crawler.var(sourceVarName), True)

            # copying tags
            for sourceTagName, targetTagName in self.templateOption('copyTag', crawler).items():
                newCrawler.setTag(targetTagName, crawler.tag(sourceTagName))

            result.append(newCrawler)

        return result


# registering task
Task.register(
    'copy',
    CopyTask
)

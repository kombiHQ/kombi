from ..Task import Task
from ...Element.Fs.FsElement import FsElement
from glob import glob

class GlobTask(Task):
    """
    Glob task used to collect files and directories.

    The target in this task can be represented using fnmatch pattern. For instance:
        "/a/**/*.exr"
    Would resolve to:
        "/a/file1.exr"
        "/a/b/c/file1.exr"
        "/a/b/c/file2.exr"
        ...
    """

    def __init__(self, *args, **kwargs):
        """
        Create a Glob task.
        """
        super(GlobTask, self).__init__(*args, **kwargs)

        # option used to skip duplicated files that can occur
        # when running glob for each target
        self.setOption(
            'skipDuplicated',
            True
        )

    def _perform(self):
        """
        Perform the task.
        """
        result = []
        alreadyAdded = set()
        targets = set()
        for element in self.elements():
            filePath = self.target(element)
            if self.option('skipDuplicated') and filePath in targets:
                continue
            targets.add(filePath)

            for resolvedFilePath in glob(filePath, recursive=True):
                # skipping duplicated results
                if self.option('skipDuplicated') and resolvedFilePath in alreadyAdded:
                    continue
                alreadyAdded.add(resolvedFilePath)

                result.append(
                    FsElement.createFromPath(resolvedFilePath)
                )

        return [y for x in FsElement.group(result) for y in x]


# registering task
Task.register(
    'glob',
    GlobTask
)

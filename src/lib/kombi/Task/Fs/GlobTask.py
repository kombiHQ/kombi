import sys
from ..Task import Task
from ...Crawler.Fs.FsCrawler import FsCrawler

# python 2 does not support recursion in the glob syntax
if sys.version_info[0] < 3:
    from kombithirdparty.glob2 import glob
else:
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
        for crawler in self.crawlers():
            filePath = self.target(crawler)

            for resolvedFilePath in glob(filePath, recursive=True):
                # skipping duplicated results
                if self.option('skipDuplicated') and resolvedFilePath in alreadyAdded:
                    continue
                alreadyAdded.add(resolvedFilePath)

                result.append(
                    FsCrawler.createFromPath(resolvedFilePath)
                )

        return result


# registering task
Task.register(
    'glob',
    GlobTask
)

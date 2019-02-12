from ...Crawler.Fs import File
from ..Task import Task
from .CreateData import CreateData

class AppendToVersion(CreateData):
    """
    Task for appending data to a version.
    """

    def rootPath(self):
        """
        Return the root path where the data directory and json files should exist.
        """
        assert self.crawlers(), "Need input crawlers to figure out root path."
        return self.crawlers()[0].var("versionPath")

    def _perform(self):
        """
        Perform the task.
        """
        for crawler in self.crawlers():
            if isinstance(crawler, File):
                self.addFile(crawler.var("filePath"))

        return super(AppendToVersion, self)._perform()


# registering task
Task.register(
    'appendToVersion',
    AppendToVersion
)

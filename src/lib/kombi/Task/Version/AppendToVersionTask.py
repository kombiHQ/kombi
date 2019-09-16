from ...Crawler.Fs import FileCrawler
from ..Task import Task
from .CreateDataTask import CreateDataTask

class AppendToVersionTask(CreateDataTask):
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
            if isinstance(crawler, FileCrawler):
                self.addFile(crawler.var("filePath"))

        return super(AppendToVersionTask, self)._perform()


# registering task
Task.register(
    'appendToVersion',
    AppendToVersionTask
)

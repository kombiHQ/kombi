from ...Element.Fs import FileElement
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
        assert self.elements(), "Need input elements to figure out root path."
        return self.elements()[0].var("versionPath")

    def _perform(self):
        """
        Perform the task.
        """
        for element in self.elements():
            if isinstance(element, FileElement):
                self.addFile(element.var("filePath"))

        return super(AppendToVersionTask, self)._perform()


# registering task
Task.register(
    'appendToVersion',
    AppendToVersionTask
)

from ...InfoCrate.Fs import FileInfoCrate
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
        assert self.infoCrates(), "Need input infoCrates to figure out root path."
        return self.infoCrates()[0].var("versionPath")

    def _perform(self):
        """
        Perform the task.
        """
        for infoCrate in self.infoCrates():
            if isinstance(infoCrate, FileInfoCrate):
                self.addFile(infoCrate.var("filePath"))

        return super(AppendToVersionTask, self)._perform()


# registering task
Task.register(
    'appendToVersion',
    AppendToVersionTask
)

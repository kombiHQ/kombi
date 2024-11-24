import os
import time
from ..Task import Task
from ...InfoCrate.Fs import FsInfoCrate
from ...Template import Template
from .CreateDataTask import CreateDataTask

class CreateVersionTask(CreateDataTask):
    """
    ABC for creating a version.
    """

    __genericInfoCrateInfo = [
        "job",
        "seq",
        "shot",
        "assetName",
        "step",
        "variant"
    ]

    def __init__(self, *args, **kwargs):
        """
        Create a version.
        """
        super(CreateVersionTask, self).__init__(*args, **kwargs)

        self.setOption('versionPattern', '')
        self.__startTime = time.time()
        self.__loadedStaticData = False

    def version(self):
        """
        Return an integer containing the published version.
        """
        return self.__version

    def versionPath(self):
        """
        Return the path for the version base folder.
        """
        return self.rootPath()

    def versionName(self):
        """
        Return the name of the version base folder.
        """
        return os.path.basename(self.versionPath())

    def add(self, *args, **kwargs):
        """
        Cache the static information about the first infoCrate you add.
        """
        super(CreateVersionTask, self).add(*args, **kwargs)

        # make sure to do not create any files/directories at this point, since this call does not guarantee
        # the task is going to be executed right away (since tasks can be serialized).
        self.__loadStaticData()

    def output(self):
        """
        Run the task.

        We need to wrap this call to make sure the versionPath is created before
        any of the sub-classes try to write to it through _perform.
        """
        os.makedirs(self.versionPath())

        return super(CreateVersionTask, self).output()

    def _perform(self):
        """
        Perform the task.
        """
        super(CreateVersionTask, self)._perform()

        # Find all the infoCrates for data that was created for this version
        infoCrate = FsInfoCrate.createFromPath(self.dataPath())
        dataInfoCrates = infoCrate.glob()

        # Add json files
        for jsonFile in ["info.json", "data.json", "env.json"]:
            dataInfoCrates.append(FsInfoCrate.createFromPath(os.path.join(self.versionPath(), jsonFile)))

        # Add context variables so subsequent tasks get them
        for infoCrate in dataInfoCrates:
            for var in self.__genericInfoCrateInfo:
                if var in self.infoNames():
                    infoCrate.setVar(var, self.info(var), True)
            infoCrate.setVar("versionPath", self.versionPath(), True)
            infoCrate.setVar("version", self.version(), True)
            infoCrate.setVar("versionName", self.versionName(), True)
            infoCrate.setVar("dataPath", self.dataPath(), True)

        return dataInfoCrates

    def updateInfo(self):
        """
        Write info.json file.
        """
        self.addInfo('version', self.version())
        self.addInfo('totalTime', int(time.time() - self.__startTime))

        super(CreateVersionTask, self).updateInfo()

    def __loadStaticData(self):
        """
        Load the static information about the publish.
        """
        if self.__loadedStaticData or not self.infoCrates():
            return

        self.__loadedStaticData = True

        # all infoCrates must contain the same information about assetName,
        # variant and version. For this reason looking only in the first one
        infoCrate = self.infoCrates()[0]

        # Add generic info that is expected to be on the infoCrate
        for info in self.__genericInfoCrateInfo:
            if info in infoCrate.varNames():
                self.addInfo(info, infoCrate.var(info))

        # looking for the version based on the version folder name
        # that follows the convention "v001"
        self.__version = int(
            Template.runProcedure(
                "vernumber",
                os.path.basename(self.versionPath()),
                self.option('versionPattern')
            )
        )


# registering task
Task.register(
    'createVersion',
    CreateVersionTask
)

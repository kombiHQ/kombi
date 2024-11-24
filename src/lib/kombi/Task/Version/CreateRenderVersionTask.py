import os
from ...InfoCrate.Fs import FsInfoCrate
from ...InfoCrate import InfoCrate
from ...InfoCrate.Fs.Scene import SceneInfoCrate
from ..Task import Task
from .CreateIncrementalVersionTask import CreateIncrementalVersionTask

class CreateRenderVersionTask(CreateIncrementalVersionTask):
    """
    Create texture version task.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a render version.
        """
        super(CreateRenderVersionTask, self).__init__(*args, **kwargs)

    def _perform(self):
        """
        Perform the task.
        """
        sourceScenes = set()

        for infoCrate in self.infoCrates():

            targetFile = self._computeRenderTargetLocation(infoCrate)
            # copying the render file
            self.copyFile(infoCrate.var('filePath'), targetFile)
            self.addFile(targetFile)

            # Crawl from source directory for scenes to save along with data
            infoCrate = FsInfoCrate.createFromPath(infoCrate.var('sourceDirectory'))
            sceneInfoCrates = infoCrate.glob([SceneInfoCrate])
            for sceneInfoCrate in sceneInfoCrates:
                sourceScenes.add(sceneInfoCrate.var('filePath'))

        # Copy source scenes
        for sourceScene in sourceScenes:
            targetScene = os.path.join(self.dataPath(), os.path.basename(sourceScene))
            self.copyFile(sourceScene, targetScene)
            self.addFile(targetScene)

        # Exclude all work scenes and movies from incremental versioning
        exclude = set()
        for sceneClasses in InfoCrate.registeredSubclasses(SceneInfoCrate):
            exclude.update(sceneClasses.extensions())
        exclude.add("mov")

        return super(CreateRenderVersionTask, self)._perform(incrementalExcludeTypes=list(exclude))

    def _computeRenderTargetLocation(self, infoCrate):
        """
        Compute the target file path for a render.
        """
        return os.path.join(
            self.dataPath(),
            "renders",
            "{}_{}_{}.{}.{}".format(
                infoCrate.var('shot'),
                infoCrate.var('step'),
                infoCrate.var('pass'),
                str(infoCrate.var('frame')).zfill(infoCrate.var('padding')),
                infoCrate.var('ext')
            )
        )


# registering task
Task.register(
    'createRenderVersion',
    CreateRenderVersionTask
)

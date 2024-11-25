import os
from ...Element.Fs import FsElement
from ...Element import Element
from ...Element.Fs.Scene import SceneElement
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

        for element in self.elements():

            targetFile = self._computeRenderTargetLocation(element)
            # copying the render file
            self.copyFile(element.var('filePath'), targetFile)
            self.addFile(targetFile)

            # Crawl from source directory for scenes to save along with data
            element = FsElement.createFromPath(element.var('sourceDirectory'))
            sceneElements = element.glob([SceneElement])
            for sceneElement in sceneElements:
                sourceScenes.add(sceneElement.var('filePath'))

        # Copy source scenes
        for sourceScene in sourceScenes:
            targetScene = os.path.join(self.dataPath(), os.path.basename(sourceScene))
            self.copyFile(sourceScene, targetScene)
            self.addFile(targetScene)

        # Exclude all work scenes and movies from incremental versioning
        exclude = set()
        for sceneClasses in Element.registeredSubclasses(SceneElement):
            exclude.update(sceneClasses.extensions())
        exclude.add("mov")

        return super(CreateRenderVersionTask, self)._perform(incrementalExcludeTypes=list(exclude))

    def _computeRenderTargetLocation(self, element):
        """
        Compute the target file path for a render.
        """
        return os.path.join(
            self.dataPath(),
            "renders",
            "{}_{}_{}.{}.{}".format(
                element.var('shot'),
                element.var('step'),
                element.var('pass'),
                str(element.var('frame')).zfill(element.var('padding')),
                element.var('ext')
            )
        )


# registering task
Task.register(
    'createRenderVersion',
    CreateRenderVersionTask
)

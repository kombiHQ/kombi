import os
from ...Crawler.Fs import FsPath
from ...Crawler import Crawler
from ...Crawler.Fs.Scene import Scene
from ..Task import Task
from .CreateIncrementalVersion import CreateIncrementalVersion

class CreateRenderVersion(CreateIncrementalVersion):
    """
    Create texture version task.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a render version.
        """
        super(CreateRenderVersion, self).__init__(*args, **kwargs)

    def _perform(self):
        """
        Perform the task.
        """
        sourceScenes = set()

        for crawler in self.crawlers():

            targetFile = self._computeRenderTargetLocation(crawler)
            # copying the render file
            self.copyFile(crawler.var('filePath'), targetFile)
            self.addFile(targetFile)

            # Crawl from source directory for scenes to save along with data
            crawler = FsPath.createFromPath(crawler.var('sourceDirectory'))
            sceneCrawlers = crawler.glob([Scene])
            for sceneCrawler in sceneCrawlers:
                sourceScenes.add(sceneCrawler.var('filePath'))

        # Copy source scenes
        for sourceScene in sourceScenes:
            targetScene = os.path.join(self.dataPath(), os.path.basename(sourceScene))
            self.copyFile(sourceScene, targetScene)
            self.addFile(targetScene)

        # Exclude all work scenes and movies from incremental versioning
        exclude = set()
        for sceneClasses in Crawler.registeredSubclasses(Scene):
            exclude.update(sceneClasses.extensions())
        exclude.add("mov")

        return super(CreateRenderVersion, self)._perform(incrementalExcludeTypes=list(exclude))

    def _computeRenderTargetLocation(self, crawler):
        """
        Compute the target file path for a render.
        """
        return os.path.join(
            self.dataPath(),
            "renders",
            "{}_{}_{}.{}.{}".format(
                crawler.var('shot'),
                crawler.var('step'),
                crawler.var('pass'),
                str(crawler.var('frame')).zfill(crawler.var('padding')),
                crawler.var('ext')
            )
        )


# registering task
Task.register(
    'createRenderVersion',
    CreateRenderVersion
)

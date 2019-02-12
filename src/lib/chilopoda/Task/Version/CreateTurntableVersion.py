import os
from ..Task import Task
from .CreateRenderVersion import CreateRenderVersion

class CreateTurntableVersion(CreateRenderVersion):
    """
    Create turntable version task.
    """

    def _computeRenderTargetLocation(self, crawler):
        """
        Compute the target file path for a render.
        """
        return os.path.join(
            self.dataPath(),
            "renders",
            crawler.var('pass'),
            "{}_{}_{}_{}_{}.{}.{}".format(
                crawler.var('job'),
                crawler.var('assetName'),
                crawler.var('step'),
                crawler.var('variant'),
                crawler.var('pass'),
                str(crawler.var('frame')).zfill(crawler.var('padding')),
                crawler.var('ext')
            )
        )


# registering task
Task.register(
    'createTurntableVersion',
    CreateTurntableVersion
)

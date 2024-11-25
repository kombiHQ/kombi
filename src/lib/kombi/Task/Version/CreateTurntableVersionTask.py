import os
from ..Task import Task
from .CreateRenderVersionTask import CreateRenderVersionTask

class CreateTurntableVersionTask(CreateRenderVersionTask):
    """
    Create turntable version task.
    """

    def _computeRenderTargetLocation(self, element):
        """
        Compute the target file path for a render.
        """
        return os.path.join(
            self.dataPath(),
            "renders",
            element.var('pass'),
            "{}_{}_{}_{}_{}.{}.{}".format(
                element.var('job'),
                element.var('assetName'),
                element.var('step'),
                element.var('variant'),
                element.var('pass'),
                str(element.var('frame')).zfill(element.var('padding')),
                element.var('ext')
            )
        )


# registering task
Task.register(
    'createTurntableVersion',
    CreateTurntableVersionTask
)

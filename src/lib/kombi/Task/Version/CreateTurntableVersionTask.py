import os
from ..Task import Task
from .CreateRenderVersionTask import CreateRenderVersionTask

class CreateTurntableVersionTask(CreateRenderVersionTask):
    """
    Create turntable version task.
    """

    def _computeRenderTargetLocation(self, infoCrate):
        """
        Compute the target file path for a render.
        """
        return os.path.join(
            self.dataPath(),
            "renders",
            infoCrate.var('pass'),
            "{}_{}_{}_{}_{}.{}.{}".format(
                infoCrate.var('job'),
                infoCrate.var('assetName'),
                infoCrate.var('step'),
                infoCrate.var('variant'),
                infoCrate.var('pass'),
                str(infoCrate.var('frame')).zfill(infoCrate.var('padding')),
                infoCrate.var('ext')
            )
        )


# registering task
Task.register(
    'createTurntableVersion',
    CreateTurntableVersionTask
)

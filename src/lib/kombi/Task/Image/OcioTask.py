import os
from ..Task import Task

class OcioTaskConfigurationError(Exception):
    """Invalid OCIO configuration error."""

class OcioTask(Task):
    """
    Base class used by all OCIO image tasks.

    Optional Options: "ocioConfig"
    """

    __ocioConfigDefault = ''

    def __init__(self, *args, **kwargs):
        """
        Create a OcioTask task.
        """
        super(OcioTask, self).__init__(*args, **kwargs)

        self.setOption("ocioConfig", self.__ocioConfigDefault)
        self.setMetadata('dispatch.split', True)

    def ocioConfig(self):
        """
        Return an OCIO config instance.
        """
        import PyOpenColorIO as ocio

        # open color io configuration
        if self.option('ocioConfig'):
            config = ocio.Config.CreateFromFile(self.option('ocioConfig'))

        # otherwise loading configuration from $OCIO environment variable
        elif 'OCIO' in os.environ:
            config = ocio.GetCurrentConfig()
        else:
            raise OcioTaskConfigurationError(
                'Could not find an OCIO configuration to be loaded.'
            )

        return config

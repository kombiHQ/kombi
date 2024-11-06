import os
from .TaskWrapper import TaskWrapper
from .DCCTaskWrapper import DCCTaskWrapper

class GafferTaskWrapper(DCCTaskWrapper):
    """
    Performs a task inside gaffer.
    """

    __gafferExecutable = os.environ.get(
        'KOMBI_GAFFER_EXECUTABLE',
        'gaffer'
    )

    def __init__(self, *args, **kwargs):
        super(GafferTaskWrapper, self).__init__(*args, **kwargs)

        # if 'GAFFER_PYTHONHOME' in self.option('env'):
        #     self.option('env')['PYTHONHOME'] = self.option('env')['GAFFER_PYTHONHOME']

    def _command(self):
        """
        For re-implementation: should return a string which is executed as subprocess.
        """
        scriptLoaderPath = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)
            ),
            'auxiliary',
            'gafferRunSerializedTask.py'
        )

        return '{} env python "{}"'.format(
            self.__gafferExecutable,
            scriptLoaderPath
        )

    @classmethod
    def _hookName(cls):
        """
        For re-implementation: should return a string containing the name used for the hook registered in basetools.
        """
        return "gaffer"


# registering task wrapper
TaskWrapper.register(
    'gaffer',
    GafferTaskWrapper
)

import os
import platform
import subprocess
from ..Task import Task

class RevealInFileManagerTask(Task):
    """
    Open the file manager with the input elements.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a RevealInFileManagerTask object.
        """
        super(RevealInFileManagerTask, self).__init__(*args, **kwargs)

        self.setMetadata(
            'match.vars.filePath',
            [
                '*'
            ]
        )

        self.setMetadata('ui.task.showExecutionSettings', False)

    def _perform(self):
        """
        Perform the task.
        """
        filePaths = []
        filePaths.extend(map(lambda x: x.var('filePath'), self.elements()))

        # linux <3
        args = None
        if platform.system() == 'Linux':
            args.append('nautilus')
            args += filePaths
        # windows
        elif platform.system() == 'Windows':
            args = ('explorer.exe', '/select,' + filePaths[0].replace('/', '\\'))
        # macos
        elif platform.system() == 'Darwin':
            args = ('open', filePaths)

        assert args

        env = dict(os.environ)
        if 'PYTHONHOME' in env:
            del env['PYTHONHOME']

        if 'LD_LIBRARY_PATH' in env:
            del env['LD_LIBRARY_PATH']

        subprocess.Popen(args, env=env)

        return super(RevealInFileManagerTask, self)._perform()


# registering task
Task.register(
    'revealInFileManager',
    RevealInFileManagerTask
)

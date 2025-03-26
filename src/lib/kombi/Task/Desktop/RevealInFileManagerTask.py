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

        self.setMetadata('ui.task.showTaskHolderSettings', False)
        self.setMetadata('ui.task.menuIcon', 'icons/folder.png')

    def _perform(self):
        """
        Perform the task.
        """
        filePaths = []
        filePaths.extend(map(lambda x: x.var('filePath'), self.elements()))

        # linux <3
        if platform.system() == 'Linux':
            args = []
            filePathsEncoded = ','.join(map(lambda x: f'"file://{x}"', filePaths))
            args.append('dbus-send')
            args.append('--session')
            args.append('--print-reply')
            args.append('--dest=org.freedesktop.FileManager1')
            args.append('--type=method_call')
            args.append('/org/freedesktop/FileManager1')
            args.append('org.freedesktop.FileManager1.ShowItems')
            args.append(f'array:string:{filePathsEncoded}')
            args.append('string:""')
            subprocess.Popen(' '.join(args), shell=True)

        # windows
        elif platform.system() == 'Windows':
            subprocess.Popen(('explorer.exe', '/select,' + filePaths[0].replace('/', '\\')))
        # macos
        elif platform.system() == 'Darwin':
            subprocess.Popen(('open', filePaths))

        return super(RevealInFileManagerTask, self)._perform()


# registering task
Task.register(
    'revealInFileManager',
    RevealInFileManagerTask
)

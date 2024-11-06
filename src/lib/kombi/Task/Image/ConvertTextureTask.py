import os
import subprocess
from ..Task import Task

class ConvertTextureTask(Task):
    """
    Convert texture task using maketx.
    """

    __maketxExecutable = os.environ.get('KOMBI_MAKETX_EXECUTABLE', 'maketx')

    def __init__(self, *args, **kwargs):
        """
        Create a texture version.
        """
        super(ConvertTextureTask, self).__init__(*args, **kwargs)
        self.setOption('maketxArgs', "-v -u --checknan --unpremult --oiio")
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        for crawler in self.crawlers():
            targetFilePath = self.target(crawler)

            # creating any necessary directories
            parentDirectory = os.path.dirname(targetFilePath)
            if not os.path.exists(parentDirectory):
                try:
                    os.makedirs(parentDirectory)
                except OSError:
                    pass

            # to avoid clashing with the python used
            # for maketx
            env = dict(os.environ)
            if 'PYTHONHOME' in env:
                del env['PYTHONHOME']

            # computing a mipmap version for the texture
            subprocess.call(
                '{} {} -o "{}" "{}"'.format(
                    self.__maketxExecutable,
                    self.option('maketxArgs'),
                    targetFilePath,
                    crawler.var('filePath')
                ),
                shell=True,
                env=env
            )

        return super(ConvertTextureTask, self)._perform()


# registering task
Task.register(
    'convertTexture',
    ConvertTextureTask
)

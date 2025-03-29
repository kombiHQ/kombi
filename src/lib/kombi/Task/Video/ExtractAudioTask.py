import os
import subprocess
from ..Task import Task

class ExtractAudioTask(Task):
    """
    Extract audio from a video using ffmpeg.
    """

    __ffmpegExecutable = os.environ.get('KOMBI_FFMPEG_EXECUTABLE', 'ffmpeg')
    __defaultAudioArgs = ""

    def __init__(self, *args, **kwargs):
        """
        Create a extract audio task object.
        """
        super(ExtractAudioTask, self).__init__(*args, **kwargs)
        self.setOption('audioArgs', self.__defaultAudioArgs)

    def _perform(self):
        """
        Perform the task.
        """
        audioArgs = self.option('audioArgs')

        for element in self.elements():
            targetFilePath = self.target(element)

            # creating any necessary directories
            parentDirectory = os.path.dirname(targetFilePath)
            if not os.path.exists(parentDirectory):
                try:
                    os.makedirs(parentDirectory)
                except (IOError, OSError):
                    pass

            # ffmpeg command
            ffmpegCommand = '{ffmpeg} -loglevel error {audioArgs} -i "{input}" -y -strict -2 "{output}"'.format(
                ffmpeg=self.__ffmpegExecutable,
                input=element.var('filePath'),
                output=targetFilePath,
                audioArgs=audioArgs
            )

            # calling ffmpeg
            process = subprocess.Popen(
                ffmpegCommand,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ,
                shell=True
            )

            # capturing the output
            output, errors = process.communicate()

            # in case of any errors
            if errors:
                raise Exception(errors)

        return super(ExtractAudioTask, self)._perform()


# registering task
Task.register(
    'extractAudio',
    ExtractAudioTask
)

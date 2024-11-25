import os
import subprocess
from ..Task import Task

class ConvertVideoTask(Task):
    """
    Convert a video using ffmpeg.
    """

    __ffmpegExecutable = os.environ.get('KOMBI_FFMPEG_EXECUTABLE', 'ffmpeg')
    __defaultVideoArgs = "-vcodec h264 -pix_fmt yuvj420p"
    __defaultAudioArgs = "-f lavfi -t 1 -i anullsrc=r=48000:cl=stereo -acodec aac"
    __defaultBitRate = 115

    def __init__(self, *args, **kwargs):
        """
        Create a convert video object.
        """
        super(ConvertVideoTask, self).__init__(*args, **kwargs)

        self.setOption('videoArgs', self.__defaultVideoArgs)
        self.setOption('audioArgs', self.__defaultAudioArgs)
        self.setOption('bitRate', self.__defaultBitRate)

    def _perform(self):
        """
        Perform the task.
        """
        videoArgs = self.option('videoArgs')
        audioArgs = self.option('audioArgs')
        bitRate = self.option('bitRate')

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
            ffmpegCommand = '{ffmpeg} -loglevel error {audioArgs} -i "{input}" -b {bitRate}M -minrate {bitRate}M -maxrate {bitRate}M {videoArgs} -y -strict -2 "{output}"'.format(
                ffmpeg=self.__ffmpegExecutable,
                input=element.var('filePath'),
                output=targetFilePath,
                videoArgs=videoArgs,
                bitRate=bitRate,
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

        return super(ConvertVideoTask, self)._perform()


# registering task
Task.register(
    'convertVideo',
    ConvertVideoTask
)

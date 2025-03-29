import os
import shutil
import tempfile
import subprocess
from ..Task import Task
from ...Element.Fs import FsElement

class AddAudioTrackTask(Task):
    """
    Adds a audio track to a video using ffmpeg.
    """

    __ffmpegExecutable = os.environ.get('KOMBI_FFMPEG_EXECUTABLE', 'ffmpeg')

    def __init__(self, *args, **kwargs):
        """
        Create a extract audio task object.
        """
        super(AddAudioTrackTask, self).__init__(*args, **kwargs)

        # audio control settings
        self.setOption('audioStartAt', 0.0)
        self.setOption('offset', 0.0)
        self.setOption('audioFilePath', '')
        self.setOption('audioCodec', 'aac')
        self.setOption('audioBitrate', '192k')

    def _processElement(self, element):
        """
        Process an individual element.
        """
        targetFilePath = os.path.normpath(self.target(element))
        sourceFilePath = os.path.normpath(element.var('fullPath'))
        sourceCopyFilePath = None
        audioFilePath = self.option('audioFilePath')

        # in case the source is the same as the target, making a copy of the source so
        # we can modify it
        if targetFilePath == sourceFilePath:
            newTempFile = tempfile.NamedTemporaryFile(suffix=os.path.basename(sourceFilePath))
            sourceCopyFilePath = newTempFile.name
            newTempFile.close()
            shutil.copy2(sourceFilePath, sourceCopyFilePath)
            sourceFilePath = sourceCopyFilePath

        # making sure the file exists
        assert os.path.exists(audioFilePath), "Invalid audio file path: {}".format(audioFilePath)

        # creating any necessary directories
        parentDirectory = os.path.dirname(targetFilePath)
        if not os.path.exists(parentDirectory):
            try:
                os.makedirs(parentDirectory)
            except (IOError, OSError):
                pass

        audioOffsetArgs = ""
        audioOffset = float(self.option('offset'))
        if audioOffset:
            audioOffsetArgs = '-af "adelay={offset}|{offset}"'.format(offset=int(audioOffset * 1000.0))

        # ffmpeg command
        ffmpegCommand = '{ffmpeg} -loglevel error -i "{videoInput}" -ss {audioStartAt} -i "{audioInput}" {audioOffset} -c:v copy -c:a {audioCodec} -b:a {audioBitrate} -t {duration} -y -strict -2 "{output}"'.format(
            ffmpeg=self.__ffmpegExecutable,
            videoInput=sourceFilePath,
            audioStartAt=self.option('audioStartAt'),
            audioOffset=audioOffsetArgs,
            audioInput=audioFilePath,
            audioCodec=self.option('audioCodec'),
            audioBitrate=self.option('audioBitrate'),
            duration=element.var('duration'),
            output=targetFilePath
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

        # removing any temporary file
        if sourceCopyFilePath:
            os.remove(sourceCopyFilePath)

        # in case of any errors
        if errors:
            raise Exception(errors)

        return FsElement.createFromPath(targetFilePath)


# registering task
Task.register(
    'addAudioTrack',
    AddAudioTrackTask
)

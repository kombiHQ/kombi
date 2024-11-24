import os
import json
import subprocess
from .VideoInfoCrate import VideoInfoCrate

class MovInfoCrate(VideoInfoCrate):
    """
    Mov infoCrate.
    """

    __ffprobeExecutable = os.environ.get('KOMBI_FFPROBE_EXECUTABLE', 'ffprobe')

    def var(self, name):
        """
        Return var value using lazy loading implementation for firstFrame and lastFrame.
        """
        if self.__ffprobeExecutable and name in ('firstFrame', 'lastFrame', 'duration', 'durationTs') and name not in self.varNames():
            self.__lazyInfo()

        return super(MovInfoCrate, self).var(name)

    @classmethod
    def test(cls, pathHolder, parentInfoCrate):
        """
        Test if the path holder contains a mov file.
        """
        if not super(MovInfoCrate, cls).test(pathHolder, parentInfoCrate):
            return False

        return pathHolder.ext() == 'mov'

    def __lazyInfo(self):
        """
        Query the mov info using ffprobe and set them as infoCrate variables if available.
        """
        cmd = '{} -v quiet -show_streams -print_format json "{}"'.format(
            self.__ffprobeExecutable,
            self.var('filePath')
        )

        # calling ffprobe
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ,
            shell=True
        )

        # capturing the output
        output, error = process.communicate()
        result = json.loads(output.decode("utf-8"))
        if "streams" not in result:
            return

        self.setVar('duration', float(result['streams'][0]['duration']))
        self.setVar('durationTs', int(result['streams'][0]['duration_ts']))

        tags = result['streams'][0].get("tags")
        if not tags:
            return

        startTimecode = tags.get("timecode", "0")
        nbFrames = int(result['streams'][0]['nb_frames']) - 1
        frameRateStr = result['streams'][0]['avg_frame_rate'].split("/")
        frameRate = int(float(frameRateStr[0]) / float(frameRateStr[1]))
        firstFrame = 0
        for f, t in zip((3600 * frameRate, 60 * frameRate, frameRate, 1), startTimecode.split(':')):
            firstFrame += f * int(t)

        self.setVar('firstFrame', firstFrame)
        self.setVar('lastFrame', firstFrame + nbFrames)


# registration
MovInfoCrate.register(
    'mov',
    MovInfoCrate
)

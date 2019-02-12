import os
import json
import subprocess
from .Video import Video

class Mov(Video):
    """
    Mov crawler.
    """

    __ffprobeExecutable = os.environ.get('CHILOPODA_FFPROBE_EXECUTABLE', 'ffprobe')

    def var(self, name):
        """
        Return var value using lazy loading implementation for firstFrame and lastFrame.
        """
        if self.__ffprobeExecutable and name in ('firstFrame', 'lastFrame') and name not in self.varNames():
            self.__getFirstLastFrames()

        return super(Mov, self).var(name)

    @classmethod
    def test(cls, pathHolder, parentCrawler):
        """
        Test if the path holder contains a mov file.
        """
        if not super(Mov, cls).test(pathHolder, parentCrawler):
            return False

        return pathHolder.ext() == 'mov'

    def __getFirstLastFrames(self):
        """
        Query first frame and last frame using ffprobe and set them as crawler variables if available.
        """
        assert(self.__ffprobeExecutable)

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

        tags = result['streams'][0].get("tags")
        if not tags:
            return

        startTimecode = tags.get("timecode", "0")
        nbFrames = int(result['streams'][0]['nb_frames']) - 1
        frameRateStr = result['streams'][0]['avg_frame_rate'].split("/")
        frameRate = int(float(frameRateStr[0])/float(frameRateStr[1]))
        firstFrame = 0
        for f, t in zip((3600 * frameRate, 60 * frameRate, frameRate, 1), startTimecode.split(':')):
            firstFrame += f * int(t)

        self.setVar('firstFrame', firstFrame)
        self.setVar('lastFrame', firstFrame + nbFrames)


# registration
Mov.register(
    'mov',
    Mov
)

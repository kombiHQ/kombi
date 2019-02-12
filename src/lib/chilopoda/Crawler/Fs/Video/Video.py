import subprocess
import os
import json
from ..File import File

class Video(File):
    """
    Abstracted video crawler.
    """

    __ffprobeExecutable = os.environ.get('CHILOPODA_FFPROBE_EXECUTABLE', 'ffprobe')

    def __init__(self, *args, **kwargs):
        """
        Create a video crawler.
        """
        super(Video, self).__init__(*args, **kwargs)

        self.setVar('category', 'video')

        # setting a video tag
        self.setTag(
            'video',
            self.pathHolder().baseName()
        )

    def var(self, name):
        """
        Return var value using lazy loading implementation for width and height.
        """
        if self.__ffprobeExecutable and name in ('width', 'height') and name not in self.varNames():
            self.__computeWidthHeight()

        return super(Video, self).var(name)

    def __computeWidthHeight(self):
        """
        Query width and height using ffprobe and set them as crawler variables.
        """
        # Get width and height from movie using ffprobe
        cmd = '{} -v quiet -print_format json -show_entries stream=height,width "{}"'.format(
            self. __ffprobeExecutable,
            self.var('filePath')
        )

        # calling ffmpeg
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
        if "streams" in result:
            self.setVar('width', result['streams'][0]['width'])
            self.setVar('height', result['streams'][0]['height'])

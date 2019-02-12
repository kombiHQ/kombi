import os
import json
import subprocess
from ..File import File

class Image(File):
    """
    Abstracted image crawler.
    """

    __ffprobeExecutable = os.environ.get('CHILOPODA_FFPROBE_EXECUTABLE', 'ffprobe')

    def __init__(self, *args, **kwargs):
        """
        Create an image crawler.
        """
        super(Image, self).__init__(*args, **kwargs)

        self.setVar('category', 'image')

        # setting a video tag
        self.setVar('imageType', 'single')

        self.__computeImageSequence()

    def isSequence(self):
        """
        Return if path holder is holding a file that is part of a image sequence.
        """
        # first test is to test against the conventional image seq abc.0001.ext
        isImageSeq = self.__isStandardSequence()

        # second test is to check against the non-conventional image seq abc_0001.ext
        if not isImageSeq:
            isImageSeq = self.__isAmbiguousSequence()

        return isImageSeq

    def var(self, name):
        """
        Return var value using lazy loading implementation for width and height.
        """
        if self.__ffprobeExecutable and name in ('width', 'height') and name not in self.varNames():
            self.__computeWidthHeight()

        return super(Image, self).var(name)

    def __computeImageSequence(self):
        """
        Compute the image sequence tags and vars.
        """
        nameParts = self.pathHolder().baseName().split(".")
        frame = None
        name = None
        frameSep = None
        if self.__isStandardSequence():
            frame = nameParts[-2]
            name = '.'.join(nameParts[:-2])
            frameSep = "."
        elif self.__isAmbiguousSequence():
            nameParts = nameParts[0].split("_")
            frame = nameParts[-1]
            name = '_'.join(nameParts[:-1])
            frameSep = "_"

        if frame is not None:
            self.setVar('imageType', 'sequence')
            self.setVar('name', name)
            self.setVar('frame', int(frame))
            self.setVar('padding', len(frame))

            # image sequence tag:
            # this information is used to group files, we don't necessary
            # need to obey the information about the padding from the file itself,
            # since the sequence can be unpadded.
            self.setTag(
                'group',
                '{0}{1}{2}.{3}'.format(
                    name,
                    frameSep,
                    '#' * len(frame),
                    self.var('ext')
                )
            )
        else:
            self.setTag('image', self.pathHolder().baseName())

    def __isStandardSequence(self):
        """
        Return a boolean telling if the crawler contains a standard image sequence.

        The crawler must follow the standard seq convention: abc.0001.ext
        """
        nameParts = self.pathHolder().baseName().split(".")
        isImageSeq = (len(nameParts) >= 3 and self.pathHolder().baseName().split(".")[-2].isdigit())

        return isImageSeq

    def __isAmbiguousSequence(self):
        """
        Return a boolean telling if the crawler contains an ambiguous image sequence.

        This crawler must follow the ambiguous seq convention: abc_0001.ext
        """
        nameParts = self.pathHolder().baseName().split(".")
        parts = nameParts[0].split("_")
        isImageSeq = False
        if len(parts) > 1:
            isImageSeq = (parts[-1].isdigit() and len(parts[-1]) >= 4)

        return isImageSeq

    def __computeWidthHeight(self):
        """
        Query width and height using ffprobe and set them as crawler variables.
        """
        # Get width and height from movie using ffprobe
        cmd = '{} -v quiet -print_format json -show_entries stream=height,width "{}"'.format(
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
        self.setVar('width', result['streams'][0]['width'])
        self.setVar('height', result['streams'][0]['height'])

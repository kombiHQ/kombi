import os
import subprocess
from collections import OrderedDict
from ..Task import Task

class FFmpeg(Task):
    """
    Abstracted ffmpeg task.

    Options:
        - optional: scale (float), videoCoded, pixelFormat and bitRate
        - required: sourceColorSpace, targetColorSpace and frameRate (float)
    """

    __ffmpegExecutable = os.environ.get('CHILOPODA_FFMPEG_EXECUTABLE', 'ffmpeg')
    __defaultScale = 1.0
    __defaultVideoCodec = "libx264"
    __defaultPixelFormat = "yuvj420p"
    __defaultBitRate = 115

    def __init__(self, *args, **kwargs):
        """
        Create a ffmpeg object.
        """
        super(FFmpeg, self).__init__(*args, **kwargs)

        self.setOption('scale', self.__defaultScale)
        self.setOption('videoCodec', self.__defaultVideoCodec)
        self.setOption('pixelFormat', self.__defaultPixelFormat)
        self.setOption('bitRate', self.__defaultBitRate)

    def _perform(self):
        """
        Perform the task.
        """
        # collecting all crawlers that have the same target file path
        movFiles = OrderedDict()
        for crawler in self.crawlers():
            targetFilePath = self.target(crawler)

            if targetFilePath not in movFiles:
                movFiles[targetFilePath] = []

            movFiles[targetFilePath].append(crawler)

        # calling ffmpeg
        for movFile in movFiles.keys():
            sequenceCrawlers = movFiles[movFile]
            crawler = sequenceCrawlers[0]

            # executing ffmpeg
            self.__executeFFmpeg(
                sequenceCrawlers,
                movFile
            )

        # default result based on the target filePath
        return super(FFmpeg, self)._perform()

    def __executeFFmpeg(self, sequenceCrawlers, outputFilePath):
        """
        Execute ffmpeg.
        """
        crawler = sequenceCrawlers[0]
        startFrame = crawler.var('frame')

        # building an image sequence name that ffmpeg understands that is a file
        # sequence (aka foo.%04d.ext)
        inputSequence = os.path.join(
            os.path.dirname(crawler.var('filePath')),
            '{name}.%0{padding}d.{ext}'.format(
                name=crawler.var('name'),
                padding=crawler.var('padding'),
                ext=crawler.var('ext')
            )
        )

        # trying to create the directory automatically in case it
        # does not exist yet
        try:
            os.makedirs(
                os.path.dirname(
                    outputFilePath
                )
            )
        except OSError:
            pass

        # arguments passed to ffmpeg
        arguments = [
            # error level
            '-loglevel error',
            # frame rate
            '-framerate {0}'.format(
                self.option('frameRate')
            ),
            # start frame
            '-start_number {0}'.format(
                startFrame
            ),
            # input sequence
            '-i "{0}"'.format(
                inputSequence
            ),
            # video codec
            '-vcodec {0}'.format(
                self.option('videoCodec')
            ),
            # bit rate
            '-b {0}M -minrate {0}M -maxrate {0}M'.format(
                self.option('bitRate')
            ),
            # target color
            '-color_primaries {0}'.format(
                self.option('targetColorSpace')
            ),
            '-colorspace {0}'.format(
                self.option('targetColorSpace')
            ),
            # source color
            '-color_trc {0}'.format(
                self.option('sourceColorSpace')
            ),
            # pixel format
            '-pix_fmt {0}'.format(
                self.option('pixelFormat')
            ),
            # scale (default 1.0)
            '-vf scale=iw*{0}:ih*{0}'.format(
                self.option('scale')
            ),
            # target mov file
            '-y "{0}"'.format(
                outputFilePath
            )
        ]

        # ffmpeg command
        ffmpegCommand = '{} {}'.format(
            self.__ffmpegExecutable,
            ' '.join(arguments),
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
        output, error = process.communicate()

        # in case of any errors
        if error:
            raise Exception(error)


# registering task
Task.register(
    'ffmpeg',
    FFmpeg
)

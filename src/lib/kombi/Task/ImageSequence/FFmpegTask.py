import os
import subprocess
from collections import OrderedDict
from ..Task import Task

class FFmpegTask(Task):
    """
    Abstracted ffmpeg task.

    Options:
        - optional: scale (float), videoCoded, pixelFormat and bitRate
        - required: sourceColorSpace, targetColorSpace and frameRate (float)
    """

    __ffmpegExecutable = os.environ.get('KOMBI_FFMPEG_EXECUTABLE', 'ffmpeg')

    def __init__(self, *args, **kwargs):
        """
        Create a ffmpeg object.
        """
        super(FFmpegTask, self).__init__(*args, **kwargs)

        self.setOption('width', "(even {width})")
        self.setOption('height', "(even {height})")
        self.setOption('videoCodec', "libx264")
        self.setOption('pixelFormat', "yuvj420p")
        self.setOption('bitRate', 115)
        self.setOption('sourceColorSpace', "linear")
        self.setOption('targetColorSpace', "bt709")
        self.setOption('frameRate', 23.976)

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
        return super(FFmpegTask, self)._perform()

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
            # resolution
            '-vf scale={0}:{1}'.format(
                self.templateOption('width', crawler),
                self.templateOption('height', crawler)
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
        env = dict(os.environ)
        if 'PYTHONHOME' in env:
            del env['PYTHONHOME']

        if 'LD_LIBRARY_PATH' in env:
            del env['LD_LIBRARY_PATH']

        process = subprocess.Popen(
            ffmpegCommand,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
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
    FFmpegTask
)

import os
import multiprocessing
from ...Template import Template
from ..Task import Task
from ... import Crawler

# compatibility with python 2/3
try:
    basestring
except NameError:
    basestring = str

class ResizeImageTask(Task):
    """
    Image resize task.

    Options:
        - Optional: "convertToRGBA"
        - Required: "width" and "height" (both support templates)

    TODO: missing to kombi metadata/source image attributes.
    """

    __defaultConvertToRGBA = False

    def __init__(self, *args, **kwargs):
        """
        Create a resize image task.
        """
        super(ResizeImageTask, self).__init__(*args, **kwargs)

        self.setOption("convertToRGBA", self.__defaultConvertToRGBA)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        import OpenImageIO as oiio

        for crawler in self.crawlers():
            width = self.option('width')
            height = self.option('height')

            # resolving template
            if isinstance(width, basestring):
                width = int(Template(width).valueFromCrawler(
                    crawler
                ))

            if isinstance(height, basestring):
                height = int(Template(height).valueFromCrawler(
                    crawler
                ))

            targetFilePath = Crawler.Fs.Image.OiioCrawler.supportedString(
                self.target(crawler)
            )

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            # opening the source image to generate a resized image
            inputImageBuf = oiio.ImageBuf(
                Crawler.Fs.Image.OiioCrawler.supportedString(
                   crawler.var('filePath')
                )
            )
            inputSpec = inputImageBuf.spec()

            # output spec
            outputSpec = oiio.ImageSpec(
                width,
                height,
                inputSpec.nchannels,
                inputSpec.format
            )

            # resized image buf
            resizedImageBuf = oiio.ImageBuf(
                outputSpec
            )

            # resizing image
            oiio.ImageBufAlgo.resize(
                resizedImageBuf,
                inputImageBuf,
                nthreads=multiprocessing.cpu_count()
            )

            # in case the convertToRGBA is enabled
            if self.option('convertToRGBA'):
                temporaryBuffer = oiio.ImageBuf()
                oiio.ImageBufAlgo.channels(
                    temporaryBuffer,
                    resizedImageBuf,
                    ("R", "G", "B", "A")
                )
                resizedImageBuf = temporaryBuffer

            # saving target resized image
            resizedImageBuf.write(
                targetFilePath
            )

        # default result based on the target filePath
        return super(ResizeImageTask, self)._perform()


# registering task
Task.register(
    'resizeImage',
    ResizeImageTask
)

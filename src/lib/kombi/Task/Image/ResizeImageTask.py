import os
import multiprocessing
from ...Template import Template
from ..Task import Task

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

        for element in self.elements():
            width = self.option('width')
            if isinstance(width, str):
                width = int(width)

            height = self.option('height')
            if isinstance(height, str):
                height = int(height)

            targetFilePath = self.target(element)

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            # opening the source image to generate a resized image
            inputImageBuf = oiio.ImageBuf(element.var('filePath'))
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
            resizedImageBuf.write(targetFilePath)

        # default result based on the target filePath
        return super(ResizeImageTask, self)._perform()


# registering task
Task.register(
    'resizeImage',
    ResizeImageTask
)

import os
import multiprocessing

from ..Task import Task, TaskError
from ...Element.Fs import FsElement

class ConvertImageTaskError(TaskError):
    """Convert image task error."""

class ConvertImageTask(Task):
    """
    Task used to convert an image to a different size, format and colorspace.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a resize image task.
        """
        super(ConvertImageTask, self).__init__(*args, **kwargs)

        # options used for resizing (the resize happens in case
        # the resize values are different from the original
        # element values)
        self.setOption('width', '{width}')
        self.setOption('height', '{height}')
        self.setOption('keepAspectRatio', False)

        # options used for colorspace: Linear, sRGB (etc)
        self.setOption('sourceColorspace', '')
        self.setOption('targetColorspace', '')
        self.setOption('colorConfig', '')

        # option used to convert the output to specific channels aka: ('R', 'G', 'B')
        self.setOption('convertToChannels', tuple())

        # option used to tell if the convert image should fallback to the
        # first channel when trying to convert specific channels (aka RGB)
        self.setOption('convertToChannelsFallbackToFirstChannel', True)

        # option used to convert the output to RGBA
        self.setOption('convertToRGBA', False)

        self.setMetadata('dispatch.split', True)

        # template options
        for optionName in ('width', 'height', 'targetColorspace', 'sourceColorspace', 'colorConfig'):
            self.setMetadata(f'task.options.{optionName}.template', True)

    def _processElement(self, element):
        """
        Process an individual element.
        """
        import OpenImageIO as oiio

        targetFilePath = self.target(element)

        # opening the source image
        inputImageBuf = oiio.ImageBuf(element.var('filePath'))

        # output image buf
        outImageBuf = inputImageBuf

        # resizing image
        width = int(self.option('width'))
        height = int(self.option('height'))

        if width != element.var('width') or height != element.var('height'):
            # figuring out aspect ratio used for the resizing
            ratio = None
            if int(self.option('keepAspectRatio')):
                ratio = self.__aspectRatio(
                    element.var('width'),
                    element.var('height'),
                    width,
                    height
                )

            outImageBuf = oiio.ImageBuf(
                oiio.ImageSpec(
                    int(element.var('width') * ratio) if ratio is not None else width,
                    int(element.var('height') * ratio) if ratio is not None else height,
                    inputImageBuf.spec().nchannels,
                    inputImageBuf.spec().format
                )
            )

            oiio.ImageBufAlgo.resize(
                outImageBuf,
                inputImageBuf,
                roi=outImageBuf.roi,
                nthreads=multiprocessing.cpu_count()
            )

        # in case the convert to RGBA is enabled
        if self.option('convertToRGBA') or self.option('convertToChannels'):
            useChannels = []
            requestedChannels = list(map(lambda x: str(x).upper(), ("R", "G", "B", "A") if self.option('convertToRGBA') else tuple(self.option('convertToChannels'))))
            for channelname in inputImageBuf.spec().channelnames:
                if channelname.upper() in requestedChannels:
                    useChannels.append(channelname)

            if not useChannels and self.option('convertToChannelsFallbackToFirstChannel'):
                useChannels.append(inputImageBuf.spec().channelnames[0])

            temporaryBuffer = oiio.ImageBuf()
            oiio.ImageBufAlgo.channels(
                temporaryBuffer,
                outImageBuf,
                tuple(useChannels)
            )
            outImageBuf = temporaryBuffer

        # changing colorspace
        targetColorspace = self.option('targetColorspace')
        if targetColorspace:
            oiio.ImageBufAlgo.colorconvert(
                outImageBuf,
                outImageBuf,
                self.option('sourceColorspace'),
                targetColorspace,
                colorconfig=self.option('colorConfig')
            )

        # trying to create the directory automatically in case
        # it does not exist
        try:
            os.makedirs(os.path.dirname(targetFilePath))
        except (IOError, OSError):
            pass

        # saving target output image
        if not outImageBuf.write(targetFilePath):
            raise ConvertImageTaskError(
                outImageBuf.geterror()
            )

        return FsElement.createFromPath(targetFilePath)

    def __aspectRatio(self, currentWidth, currentHeigth, newWidth, newHeight):
        """
        Return the aspect ratio used for resizing.
        """
        ratioWidth = newWidth / float(currentWidth)
        ratioHeight = newHeight / float(currentHeigth)

        # smaller ratio will ensure that the image fits in the view
        return ratioWidth if ratioWidth < ratioHeight else ratioHeight


# registering task
Task.register(
    'convertImage',
    ConvertImageTask
)

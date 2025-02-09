import os
from ..Task import Task
from ... import Element
from ...Element.Fs import FsElement

class FrameImageTask(Task):
    """
    Generates a framed image that combines the header, main image and footer.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a frame image object.
        """
        super(FrameImageTask, self).__init__(*args, **kwargs)

        self.setOption('enableHeader', True)
        self.setOption('enableFooter', True)
        self.setOption('enableWatermark', True)
        self.setOption('enableBurnin', True)

        self.setOption('headerFilePath', '')
        self.setOption('footerFilePath', '')
        self.setOption('watermarkFilePath', '')

        # hex background color in RGBA
        self.setOption('bgColor', '000000FF')

        # burn-in text
        self.setOption(
            'burnin',
            {
                'text': '',
                'x': 50,
                'y': 100,
                'color': 'ff5400FF',
                'size': 20,
                'font': ''
            }
        )

        # this option controls if the header, content and footer
        # are going to be distributed following a diagonal layout
        # header top left, content in middle and footer at
        # bottom right. Otherwise, if this option is disabled
        # the elements are distributed from the top to the bottom
        # aligned to the center.
        self.setOption('diagonalLayout', True)

        # adding template support for all options
        for optionName in self.optionNames():
            self.setMetadata(f'task.options.{optionName}.template', True)

        self.setMetadata('dispatch.split', True)

    def _processElement(self, element):
        """
        Process an individual element.
        """
        import OpenImageIO as oiio

        targetFilePath = self.target(element)

        # opening source image
        inputImageBuf = self.__toImageBuf(element.var('filePath'))
        width = inputImageBuf.spec().width

        headerImageBuf = self.option('headerFilePath') if int(self.option('enableHeader')) else None
        headerHeight = 0
        if headerImageBuf:
            headerImageBuf = self.__toImageBuf(headerImageBuf)
            headerHeight = headerImageBuf.spec().height
            width = max(width, headerImageBuf.spec().width)

        footerHeight = 0
        footerImageBuf = self.option('footerFilePath') if int(self.option('enableFooter')) else None
        if footerImageBuf:
            footerImageBuf = self.__toImageBuf(footerImageBuf)
            footerHeight = footerImageBuf.spec().height
            width = max(width, footerImageBuf.spec().width)

        # output spec
        outputSpec = oiio.ImageSpec(
            width,
            inputImageBuf.spec().height + headerHeight + footerHeight,
            inputImageBuf.spec().nchannels,
            inputImageBuf.spec().format
        )

        # output image buf
        outputImageBuf = oiio.ImageBuf(
            outputSpec
        )

        # background color
        bgColor = self.__fromHexColor(self.option('bgColor'))

        # filling background color
        oiio.ImageBufAlgo.fill(outputImageBuf, bgColor)

        # header
        if headerImageBuf:
            oiio.ImageBufAlgo.paste(
                outputImageBuf,
                0 if int(self.option('diagonalLayout')) else int((width - headerImageBuf.spec().width) / 2),
                0,
                0,
                0,
                headerImageBuf
            )

        # watermark
        watermarkImage = self.option('watermarkFilePath') if int(self.option('enableWatermark')) else None
        if watermarkImage:
            inputImageBuf = self.__watermark(inputImageBuf, self.__toImageBuf(watermarkImage))

        # content
        oiio.ImageBufAlgo.paste(
            outputImageBuf,
            int((width - inputImageBuf.spec().width) / 2),
            headerHeight,
            0,
            0,
            inputImageBuf
        )

        # footer
        if footerImageBuf:
            oiio.ImageBufAlgo.paste(
                outputImageBuf,
                width - footerImageBuf.spec().width if int(self.option('diagonalLayout')) else int((width - footerImageBuf.spec().width) / 2),
                headerHeight + inputImageBuf.spec().height,
                0,
                0,
                footerImageBuf
            )

        # burn-in text
        burnin = self.option('burnin')
        if int(self.option('enableBurnin')) and burnin['text']:
            oiio.ImageBufAlgo.render_text(
                outputImageBuf,
                int(burnin['x']),
                int(burnin['y']),
                Element.Fs.Image.OiioElement.supportedString(burnin['text']),
                int(burnin['size']),
                Element.Fs.Image.OiioElement.supportedString(burnin['font']),
                self.__fromHexColor(burnin['color'])
            )

        # making parent directories if necessary
        try:
            os.makedirs(os.path.dirname(targetFilePath))
        except (IOError, OSError):
            pass

        # writing file
        outputImageBuf.write(
            targetFilePath
        )

        return FsElement.createFromPath(targetFilePath)

    @classmethod
    def __watermark(cls, targetImageBuf, watermarkImageBuf):
        """
        Add a watermark over the target image buf.
        """
        import OpenImageIO as oiio

        outputImageBuf = oiio.ImageBuf()
        oiio.ImageBufAlgo.channels(
            outputImageBuf,
            targetImageBuf,
            ("R", "G", "B", "A")
        )

        watermarkContentBuf = oiio.ImageBuf(
            outputImageBuf.spec()
        )

        for x in range(int(watermarkContentBuf.spec().width / watermarkImageBuf.spec().width + 1)):
            for y in range(int(watermarkContentBuf.spec().height / watermarkImageBuf.spec().height + 1)):
                oiio.ImageBufAlgo.paste(
                    watermarkContentBuf,
                    int(watermarkImageBuf.spec().width * x),
                    int(watermarkImageBuf.spec().height * y),
                    0,
                    0,
                    watermarkImageBuf
                )

        oiio.ImageBufAlgo.over(outputImageBuf, watermarkContentBuf, outputImageBuf)

        return outputImageBuf

    @classmethod
    def __fromHexColor(cls, hexColor):
        """
        Convert from hex color to oiio color.
        """
        return tuple(int(hexColor[i:i + 2], 16) / 255.0 for i in (0, 2, 4, 6))

    @classmethod
    def __toImageBuf(cls, filePath):
        """
        Load the input image in open image io.
        """
        import OpenImageIO as oiio

        return oiio.ImageBuf(
            Element.Fs.Image.OiioElement.supportedString(
                filePath
            )
        )


# registering task
Task.register(
    'frameImage',
    FrameImageTask
)

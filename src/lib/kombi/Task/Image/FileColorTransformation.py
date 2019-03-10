import os
from array import array
from .UpdateImageMetadata import UpdateImageMetadata
from .Ocio import Ocio
from ..Task import Task
from ... import Crawler

class FileColorTransformation(Ocio):
    """
    Applies a color transformation to an image using open color io and open image io.

    Required Options: "sourceColorSpace", "targetColorSpace" and "lut"
    """

    def _perform(self):
        """
        Perform the task.
        """
        import OpenImageIO as oiio
        import PyOpenColorIO as ocio

        sourceColorSpace = self.option('sourceColorSpace')
        targetColorSpace = self.option('targetColorSpace')
        metadata = {
            'sourceColorSpace': sourceColorSpace,
            'targetColorSpace': targetColorSpace
        }

        # open color io configuration
        config = self.ocioConfig()

        for crawler in self.crawlers():
            # resolving the lut path
            lut = self.templateOption('lut', crawler=crawler)

            # adding color space transform
            groupTransform = ocio.GroupTransform()
            groupTransform.push_back(
                ocio.ColorSpaceTransform(
                    src=sourceColorSpace,
                    dst=targetColorSpace
                )
            )

            # adding lut transform
            groupTransform.push_back(
                 ocio.FileTransform(
                    lut,
                    interpolation=ocio.Constants.INTERP_LINEAR
                 )
            )

            # source image
            sourceImage = oiio.ImageInput.open(
                Crawler.Fs.Image.Oiio.supportedString(
                    crawler.var('filePath')
                )
            )
            spec = sourceImage.spec()
            spec.set_format(oiio.FLOAT)

            metadata['lutFile'] = lut

            pixels = sourceImage.read_image()
            sourceImage.close()

            transformedPixels = config.getProcessor(
                groupTransform
            ).applyRGB(pixels)

            targetFilePath = Crawler.Fs.Image.Oiio.supportedString(
                self.target(crawler)
            )

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            targetImage = oiio.ImageOutput.create(targetFilePath)

            # kombi metadata information
            UpdateImageMetadata.updateDefaultMetadata(
                spec,
                crawler,
                metadata
            )

            success = targetImage.open(
                targetFilePath,
                spec,
                oiio.Create
            )

            # saving target image
            if success:
                writePixels = array('d')
                writePixels.fromlist(transformedPixels)
                targetImage.write_image(writePixels)
            else:
                raise Exception(oiio.geterror())

        # default result based on the target filePath
        return super(FileColorTransformation, self)._perform()


# registering task
Task.register(
    'fileColorTransformation',
    FileColorTransformation
)

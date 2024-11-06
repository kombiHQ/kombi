import os
from array import array
from .UpdateImageMetadataTask import UpdateImageMetadataTask
from .OcioTask import OcioTask
from ..Task import Task
from ... import Crawler

class ColorTransformationTask(OcioTask):
    """
    Applies a color transformation to an image using open color io and open image io.

    Required Options: "sourceColorSpace" and "targetColorSpace".
    """

    def _perform(self):
        """
        Perform the task.
        """
        import OpenImageIO as oiio

        # open color io configuration
        config = self.ocioConfig()

        sourceColorSpace = self.option('sourceColorSpace')
        targetColorSpace = self.option('targetColorSpace')
        metadata = {
            'sourceColorSpace': sourceColorSpace,
            'targetColorSpace': targetColorSpace
        }

        for crawler in self.crawlers():

            sourceImage = oiio.ImageInput.open(
                Crawler.Fs.Image.OiioCrawler.supportedString(
                    crawler.var('filePath')
                )
            )
            spec = sourceImage.spec()
            spec.set_format(oiio.FLOAT)

            pixels = sourceImage.read_image()
            sourceImage.close()

            transformedPixels = config.getProcessor(
                sourceColorSpace,
                targetColorSpace
            ).applyRGB(pixels)

            targetFilePath = Crawler.Fs.Image.OiioCrawler.supportedString(
                self.target(crawler)
            )

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            targetImage = oiio.ImageOutput.create(
                targetFilePath
            )

            # kombi metadata information
            UpdateImageMetadataTask.updateMetadata(
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
        return super(ColorTransformationTask, self)._perform()


# registering task
Task.register(
    'colorTransformation',
    ColorTransformationTask
)

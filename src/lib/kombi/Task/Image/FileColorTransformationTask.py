import os
from array import array
from .UpdateImageMetadataTask import UpdateImageMetadataTask
from .OcioTask import OcioTask
from ..Task import Task
from ... import Element

class FileColorTransformationTask(OcioTask):
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

        for element in self.elements():
            # resolving the lut path
            lut = self.templateOption('lut', element=element)

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
                Element.Fs.Image.OiioElement.supportedString(
                    element.var('filePath')
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

            targetFilePath = Element.Fs.Image.OiioElement.supportedString(
                self.target(element)
            )

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            targetImage = oiio.ImageOutput.create(targetFilePath)

            # kombi metadata information
            UpdateImageMetadataTask.updateMetadata(
                spec,
                element,
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
        return super(FileColorTransformationTask, self)._perform()


# registering task
Task.register(
    'fileColorTransformationTask',
    FileColorTransformationTask
)

import os
from ..Task import Task
from .UpdateImageMetadata import UpdateImageMetadata
from ... import Crawler

class ConvertImage(Task):
    """
    Convert the source image (from the crawler) to the target one using oiio.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a ConvertImage task.
        """
        super(ConvertImage, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        import OpenImageIO as oiio

        for crawler in self.crawlers():

            targetFilePath = Crawler.Fs.Image.Oiio.supportedString(
                self.target(crawler)
            )

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            # converting image using open image io
            inputImageFilePath = Crawler.Fs.Image.Oiio.supportedString(
                crawler.var('filePath')
            )
            imageInput = oiio.ImageInput.open(inputImageFilePath)
            inputSpec = imageInput.spec()

            # updating chilopoda metadata
            UpdateImageMetadata.updateDefaultMetadata(inputSpec, crawler)

            outImage = oiio.ImageOutput.create(targetFilePath)
            outImage.open(
                targetFilePath,
                inputSpec,
                oiio.ImageOutputOpenMode.Create
            )

            outImage.copy_image(imageInput)
            outImage.close()

        # default result based on the target filePath
        return super(ConvertImage, self)._perform()


# registering task
Task.register(
    'convertImage',
    ConvertImage
)

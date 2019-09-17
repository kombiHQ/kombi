import os
from ..Task import Task
from .UpdateImageMetadataTask import UpdateImageMetadataTask
from ... import Crawler

class ConvertImageTask(Task):
    """
    Convert the source image (from the crawler) to the target one using oiio.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a ConvertImage task.
        """
        super(ConvertImageTask, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        import OpenImageIO as oiio

        for crawler in self.crawlers():

            targetFilePath = Crawler.Fs.Image.OiioCrawler.supportedString(
                self.target(crawler)
            )

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            # converting image using open image io
            inputImageFilePath = Crawler.Fs.Image.OiioCrawler.supportedString(
                crawler.var('filePath')
            )
            imageInput = oiio.ImageInput.open(inputImageFilePath)
            inputSpec = imageInput.spec()

            # updating kombi metadata
            UpdateImageMetadataTask.updateDefaultMetadata(inputSpec, crawler)

            outImage = oiio.ImageOutput.create(targetFilePath)

            # in case we are using an older version of oiio we need to
            # provide an additional argument to the open
            outImageOpenArgs = [
                targetFilePath,
                inputSpec
            ]
            if hasattr(oiio, 'ImageOutputOpenMode'):
                outImageOpenArgs.append(oiio.ImageOutputOpenMode.Create)

            outImage.open(
                *outImageOpenArgs
            )

            outImage.copy_image(imageInput)
            outImage.close()

        # default result based on the target filePath
        return super(ConvertImageTask, self)._perform()


# registering task
Task.register(
    'convertImage',
    ConvertImageTask
)

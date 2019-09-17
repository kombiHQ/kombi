from datetime import datetime
from ..Task import Task
from ... import Crawler

class UpdateImageMetadataTask(Task):
    """
    Updates the image metadata using oiio.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a UpdateImageMetadata task.
        """
        super(UpdateImageMetadataTask, self).__init__(*args, **kwargs)
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

            # converting image using open image io
            inputImageFilePath = Crawler.Fs.Image.OiioCrawler.supportedString(
                crawler.var('filePath')
            )
            imageInput = oiio.ImageInput.open(inputImageFilePath)
            inputSpec = imageInput.spec()

            # updating kombi metadata
            self.updateDefaultMetadata(inputSpec, crawler)

            # writing image with updated metadata
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
        return super(UpdateImageMetadataTask, self)._perform()

    @classmethod
    def updateDefaultMetadata(cls, spec, crawler, customMetadata={}):
        """
        Update the spec with the image metadata information.
        """
        defaultMetadata = {
            'sourceFile': Crawler.Fs.Image.OiioCrawler.supportedString(
                crawler.var('filePath')
            ),
            'fileUpdatedTime': Crawler.Fs.Image.OiioCrawler.supportedString(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        }

        # default metadata
        for name, value in defaultMetadata.items():
            spec.attribute(
                'kombi:{0}'.format(name),
                Crawler.Fs.Image.OiioCrawler.supportedString(
                    value
                )
            )

        # custom metadata
        for name, value in customMetadata.items():
            spec.attribute(
                'kombi:{0}'.format(name),
                Crawler.Fs.Image.OiioCrawler.supportedString(
                    value
                )
            )


# registering task
Task.register(
    'updateImageMetadata',
    UpdateImageMetadataTask
)

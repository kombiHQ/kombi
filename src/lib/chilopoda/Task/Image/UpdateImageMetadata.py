from datetime import datetime
from ..Task import Task
from ... import Crawler

class UpdateImageMetadata(Task):
    """
    Updates the image metadata using oiio.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a UpdateImageMetadata task.
        """
        super(UpdateImageMetadata, self).__init__(*args, **kwargs)
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

            # converting image using open image io
            inputImageFilePath = Crawler.Fs.Image.Oiio.supportedString(
                crawler.var('filePath')
            )
            imageInput = oiio.ImageInput.open(inputImageFilePath)
            inputSpec = imageInput.spec()

            # updating chilopoda metadata
            self.updateDefaultMetadata(inputSpec, crawler)

            # writing image with updated metadata
            outImage = oiio.ImageOutput.create(targetFilePath)
            outImage.open(
                targetFilePath,
                inputSpec,
                oiio.ImageOutputOpenMode.Create
            )

            outImage.copy_image(imageInput)
            outImage.close()

        # default result based on the target filePath
        return super(UpdateImageMetadata, self)._perform()

    @classmethod
    def updateDefaultMetadata(cls, spec, crawler, customMetadata={}):
        """
        Update the spec with the image metadata information.
        """
        defaultMetadata = {
            'sourceFile': Crawler.Fs.Image.Oiio.supportedString(
                crawler.var('filePath')
            ),
            'fileUpdatedTime': Crawler.Fs.Image.Oiio.supportedString(
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
        }

        # default metadata
        for name, value in defaultMetadata.items():
            spec.attribute(
                'chilopoda:{0}'.format(name),
                Crawler.Fs.Image.Oiio.supportedString(
                    value
                )
            )

        # custom metadata
        for name, value in customMetadata.items():
            spec.attribute(
                'chilopoda:{0}'.format(name),
                Crawler.Fs.Image.Oiio.supportedString(
                    value
                )
            )


# registering task
Task.register(
    'updateImageMetadata',
    UpdateImageMetadata
)

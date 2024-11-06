import os
from ..Task import Task
from ...Crawler.Fs.Image.OiioCrawler import OiioCrawler

class UpdateImageMetadataTask(Task):
    """
    Updates the image metadata using oiio.

    Setting metadata:
        Each metadata should be defined inside of the data option.
    """

    __maketxExecutable = os.environ.get('KOMBI_MAKETX_EXECUTABLE', 'maketx')

    def __init__(self, *args, **kwargs):
        """
        Create a UpdateImageMetadata task.
        """
        super(UpdateImageMetadataTask, self).__init__(*args, **kwargs)
        self.setMetadata('dispatch.split', True)

        # option used to specify the metadata that should be added to the image.
        self.setOption('data', {})

    def _perform(self):
        """
        Perform the task.
        """
        import OpenImageIO as oiio

        for crawler in self.crawlers():
            targetFilePath = OiioCrawler.supportedString(
                self.target(crawler)
            )

            # converting image using open image io
            inputImageFilePath = OiioCrawler.supportedString(
                crawler.var('filePath')
            )

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            # metadata
            metadata = self.templateOption('data', crawler)

            """
            args = ''
            for key, value in metadata.items():
                args += ' --attrib "{}" "{}"'.format(
                    str(key).replace('"', '\\"'),
                    str(value).replace('"', '\\"')
                )

            # computing a mipmap version for the texture
            subprocess.call(
                '{} "{}" {} -o "{}"'.format(
                    self.__maketxExecutable,
                    inputImageFilePath,
                    args,
                    targetFilePath
                ),
                shell=True
            )
            """

            imageInput = oiio.ImageInput.open(inputImageFilePath)
            inputSpec = imageInput.spec()

            self.updateMetadata(inputSpec, crawler, metadata)

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

            if not outImage.copy_image(imageInput):
                raise Exception(outImage.geterror())

            outImage.close()

        # default result based on the target filePath
        return super(UpdateImageMetadataTask, self)._perform()

    @classmethod
    def updateMetadata(cls, spec, crawler, metadata):
        """
        Update the spec with the image metadata information.
        """
        assert isinstance(metadata, dict), \
            'metadata needs to be defined as dict!'

        for name, value in metadata.items():
            spec.attribute(
                OiioCrawler.supportedString(name),
                OiioCrawler.supportedString(value) if isinstance(value, str) else value
            )


# registering task
Task.register(
    'updateImageMetadata',
    UpdateImageMetadataTask
)

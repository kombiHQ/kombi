import os
from ..Task import Task
from ...InfoCrate.Fs.Image.OiioInfoCrate import OiioInfoCrate

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

        for infoCrate in self.infoCrates():
            targetFilePath = OiioInfoCrate.supportedString(
                self.target(infoCrate)
            )

            # converting image using open image io
            inputImageFilePath = OiioInfoCrate.supportedString(
                infoCrate.var('filePath')
            )

            # trying to create the directory automatically in case it does not exist
            try:
                os.makedirs(os.path.dirname(targetFilePath))
            except OSError:
                pass

            # metadata
            metadata = self.templateOption('data', infoCrate)

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

            self.updateMetadata(inputSpec, infoCrate, metadata)

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
    def updateMetadata(cls, spec, infoCrate, metadata):
        """
        Update the spec with the image metadata information.
        """
        assert isinstance(metadata, dict), \
            'metadata needs to be defined as dict!'

        for name, value in metadata.items():
            spec.attribute(
                OiioInfoCrate.supportedString(name),
                OiioInfoCrate.supportedString(value) if isinstance(value, str) else value
            )


# registering task
Task.register(
    'updateImageMetadata',
    UpdateImageMetadataTask
)

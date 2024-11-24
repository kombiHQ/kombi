from fnmatch import fnmatch
from ...InfoCrate.Fs.Image.OiioInfoCrate import OiioInfoCrate
from ..Task import Task, TaskError

class LoadImageMetadataTaskError(TaskError):
    """Generic load image metadata task error."""

class LoadImageMetadataTaskNotFoundError(LoadImageMetadataTaskError):
    """Load image metadata task not found error."""

class LoadImageMetadataTask(Task):
    """
    Loads the metadata as infoCrate variables.

    Reading metadata:
        Each metadata should be defined as an option with prefix "_" where the value of the
        option is used to match and retrieve the value of the metadata (it supports fnmatch syntax).
        The metadata is assigned to the infoCrate as a infoCrate variable (with the same variable
        name as the option).
    """

    def __init__(self, *args, **kwargs):
        """
        Create load metadata task object.
        """
        super(LoadImageMetadataTask, self).__init__(*args, **kwargs)

        self.setMetadata('wrapper.name', 'python')
        self.setMetadata('wrapper.options', {})
        self.setMetadata('dispatch.split', True)

        self.setOption('skipIfVarAlreadyDefined', False)
        self.setOption('errorOnNotFound', True)

    def _perform(self):
        """
        Perform the task.
        """
        import OpenImageIO as oiio

        result = []
        for infoCrate in self.infoCrates():
            newInfoCrate = infoCrate.clone()

            inputSpec = oiio.ImageInput.open(OiioInfoCrate.supportedString(infoCrate.var('fullPath'))).spec()
            for metadataName in filter(lambda x: x.startswith('_'), self.optionNames()):
                found = self.option('skipIfVarAlreadyDefined') and metadataName in infoCrate.varNames()

                if not found:
                    for attribute in inputSpec.extra_attribs:
                        if fnmatch(attribute.name, self.option(metadataName)):
                            found = True
                            newInfoCrate.setVar(metadataName, attribute.value)
                            break

                if not found and self.option('errorOnNotFound'):
                    raise LoadImageMetadataTaskNotFoundError(
                        "Could not find metadata {} ({}) in file: {}".format(
                            metadataName,
                            self.option(metadataName),
                            infoCrate.var('fullPath')
                        )
                    )

            result.append(newInfoCrate)

        return result


# registering task
Task.register(
    'loadImageMetadata',
    LoadImageMetadataTask
)

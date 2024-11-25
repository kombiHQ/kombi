from fnmatch import fnmatch
from ...Element.Fs.Image.OiioElement import OiioElement
from ..Task import Task, TaskError

class LoadImageMetadataTaskError(TaskError):
    """Generic load image metadata task error."""

class LoadImageMetadataTaskNotFoundError(LoadImageMetadataTaskError):
    """Load image metadata task not found error."""

class LoadImageMetadataTask(Task):
    """
    Loads the metadata as element variables.

    Reading metadata:
        Each metadata should be defined as an option with prefix "_" where the value of the
        option is used to match and retrieve the value of the metadata (it supports fnmatch syntax).
        The metadata is assigned to the element as a element variable (with the same variable
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
        for element in self.elements():
            newElement = element.clone()

            inputSpec = oiio.ImageInput.open(OiioElement.supportedString(element.var('fullPath'))).spec()
            for metadataName in filter(lambda x: x.startswith('_'), self.optionNames()):
                found = self.option('skipIfVarAlreadyDefined') and metadataName in element.varNames()

                if not found:
                    for attribute in inputSpec.extra_attribs:
                        if fnmatch(attribute.name, self.option(metadataName)):
                            found = True
                            newElement.setVar(metadataName, attribute.value)
                            break

                if not found and self.option('errorOnNotFound'):
                    raise LoadImageMetadataTaskNotFoundError(
                        "Could not find metadata {} ({}) in file: {}".format(
                            metadataName,
                            self.option(metadataName),
                            element.var('fullPath')
                        )
                    )

            result.append(newElement)

        return result


# registering task
Task.register(
    'loadImageMetadata',
    LoadImageMetadataTask
)

from fnmatch import fnmatch
from ...Crawler.Fs.Image.OiioCrawler import OiioCrawler
from ..Task import Task, TaskError

class LoadImageMetadataTaskError(TaskError):
    """Generic load image metadata task error."""

class LoadImageMetadataTaskNotFoundError(LoadImageMetadataTaskError):
    """Load image metadata task not found error."""

class LoadImageMetadataTask(Task):
    """
    Loads the metadata as crawler variables.

    Reading metadata:
        Each metadata should be defined as an option with prefix "_" where the value of the
        option is used to match and retrieve the value of the metadata (it supports fnmatch syntax).
        The metadata is assigned to the crawler as a crawler variable (with the same variable
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
        for crawler in self.crawlers():
            newCrawler = crawler.clone()

            inputSpec = oiio.ImageInput.open(OiioCrawler.supportedString(crawler.var('fullPath'))).spec()
            for metadataName in filter(lambda x: x.startswith('_'), self.optionNames()):
                found = self.option('skipIfVarAlreadyDefined') and metadataName in crawler.varNames()

                if not found:
                    for attribute in inputSpec.extra_attribs:
                        if fnmatch(attribute.name, self.option(metadataName)):
                            found = True
                            newCrawler.setVar(metadataName, attribute.value)
                            break

                if not found and self.option('errorOnNotFound'):
                    raise LoadImageMetadataTaskNotFoundError(
                        "Could not find metadata {} ({}) in file: {}".format(
                            metadataName,
                            self.option(metadataName),
                            crawler.var('fullPath')
                        )
                    )

            result.append(newCrawler)

        return result


# registering task
Task.register(
    'loadImageMetadata',
    LoadImageMetadataTask
)

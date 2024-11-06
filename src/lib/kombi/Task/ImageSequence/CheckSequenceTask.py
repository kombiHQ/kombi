import os
from fnmatch import fnmatch
from ...Task import Task, TaskError
from ...Crawler import Crawler
from ...Crawler.Fs.Image.OiioCrawler import OiioCrawler

class CheckSequenceTaskError(TaskError):
    """Base check sequence task exception."""

class CheckSequenceTaskMinimumFramesError(CheckSequenceTaskError):
    """Check sequence task minimum frames exception."""

class CheckSequenceTaskTotalFramesError(CheckSequenceTaskError):
    """Check sequence task total frames exception."""

class CheckSequenceTaskMissingFrameError(CheckSequenceTaskError):
    """Check sequence task missing frame exception."""

class CheckSequenceTaskMinimumFileSizeError(CheckSequenceTaskError):
    """Check sequence task minimum file size exception."""

class CheckSequenceTaskRequiredMetadataError(CheckSequenceTaskError):
    """Check sequence task required metadata exception."""

class CheckSequenceTask(Task):
    """
    Implements a task that verifies for common issues in image sequence crawlers.
    """

    __missingFrame = True
    __minimumFileSize = 5
    __requiredMetadata = []
    __totalFrames = -1
    __minimumFrames = 1

    def __init__(self, *args, **kwargs):
        """
        Create a check sequence task.
        """
        super(CheckSequenceTask, self).__init__(*args, **kwargs)

        # check the length of the sequence matches the total (
        # assign -1 to disable this option)
        self.setOption("totalFrames", self.__totalFrames)

        # check for the length number of frames
        self.setOption("minimumFrames", self.__minimumFrames)

        # check for missing frames
        self.setOption("missingFrame", self.__missingFrame)

        # check for the minimum file size in bytes (Assign -1 to
        # disable this option)
        self.setOption("minimumFileSize", self.__minimumFileSize)

        # check if the frame contains the required metadata
        # names (the metadata names should be defined as
        # a list). The check is done using fnmatch pattern
        self.setOption("requiredMetadata", self.__requiredMetadata)

    def _perform(self):
        """
        Implement the execution of the task.
        """
        import OpenImageIO as oiio

        for crawlerGroup in Crawler.group(self.crawlers()):
            # sorting crawlers by frame
            crawlerGroup.sort(key=lambda x: x.var('frame'))

            previousFrame = None
            previousCrawler = None

            # total frames check
            sequenceFullPath = os.path.join(
                os.path.dirname(crawlerGroup[0].var('fullPath')),
                crawlerGroup[0].tag('group')
            ).replace("\\", '/')

            # sequence total frames check
            if self.option("totalFrames") != -1 and len(crawlerGroup) != self.option("totalFrames"):
                raise CheckSequenceTaskTotalFramesError(
                    "Sequence does not match the total number of frames. It requires '{}' and contains '{}':\n    {}".format(
                        self.option("totalFrames"),
                        len(crawlerGroup),
                        sequenceFullPath
                    )
                )

            # sequence minimum frames check
            if len(crawlerGroup) < self.option("minimumFrames"):
                raise CheckSequenceTaskMinimumFileSizeError(
                    "Sequence does not match the minimum number of frames. It requires as miminum '{}' and contains '{}':\n    {}".format(
                        self.option("minimumFrames"),
                        len(crawlerGroup),
                        sequenceFullPath
                    )
                )

            for index, crawler in enumerate(crawlerGroup):
                # missing frame check
                if self.option("missingFrame"):
                    if previousFrame is None or crawler.var("frame") - previousFrame == 1:
                        previousFrame = crawler.var("frame")
                        previousCrawler = crawler
                    else:
                        raise CheckSequenceTaskMissingFrameError(
                            "Found missing frame(s) between:\n    {}\n    ???\n    {}".format(
                                previousCrawler.var('fullPath'),
                                crawler.var('fullPath')
                            )
                        )

                # minimum file size check
                if self.option("minimumFileSize") != -1 and crawler.pathHolder().size() < self.option("minimumFileSize"):
                    raise CheckSequenceTaskMinimumFileSizeError(
                        "Frame file size does not match the minimum required size (perhaps corruped):\n    {}".format(
                            crawler.var('fullPath')
                        )
                    )

                # minimum file size check
                if self.option("minimumFileSize") != -1 and crawler.pathHolder().size() < self.option("minimumFileSize"):
                    raise CheckSequenceTaskMinimumFileSizeError(
                        "Frame file size does not match the minimum required size (perhaps corruped):\n    {}".format(
                            crawler.var('fullPath')
                        )
                    )

                # required metadata check
                for requiredMetadata in self.option("requiredMetadata"):
                    inputSpec = oiio.ImageInput.open(OiioCrawler.supportedString(crawler.var("fullPath"))).spec()

                    found = False
                    for attribute in inputSpec.extra_attribs:
                        if fnmatch(attribute.name, requiredMetadata):
                            found = True
                            break
                    if not found:
                        raise CheckSequenceTaskRequiredMetadataError(
                            "Could not find the required metadata name '{}' in the frame:\n    {}".format(
                                attribute,
                                crawler.var('fullPath')
                            )
                        )

        return self.crawlers()


# registering task
Task.register(
    'checkSequence',
    CheckSequenceTask
)

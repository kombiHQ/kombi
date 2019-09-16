from ..Task import Task
from ...Crawler import Crawler
from ...Crawler.Fs import FsCrawler

# compatibility with python 2/3
try:
    from StringIO import StringIO  # python 2
except ImportError:
    from io import StringIO  # python 3
    basestring = str

class NukeSceneTask(Task):
    """
    Executes a nuke script by triggering the write nodes.

    Required options: scene (full path of nuke script)

    All options defined in the task are resolved (in case the value contains a template string)
    then assigned as global tcl variables in nuke. Therefore, you can use it to
    provide custom data to nuke.

    Since the task options are available inside nuke, it can be easily used in
    expressions, for instance the file path knob:
    /a/$myOptionName/c

    Also, startFrame, endFrame, sourceFile and targetFile are automatically
    provided as variables.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a nuke template task.
        """
        super(NukeSceneTask, self).__init__(*args, **kwargs)

        self.setMetadata("wrapper.name", "nuke")
        self.setMetadata("wrapper.options", {})
        self.setMetadata('dispatch.split', True)

    def _perform(self):
        """
        Perform the task.
        """
        import nuke

        crawlers = self.crawlers()

        # loading nuke script
        nuke.scriptOpen(self.templateOption('scene', crawlers[0]))

        createdFiles = []
        for crawlerGroup in Crawler.group(crawlers):
            startFrame = crawlerGroup[0].var('frame')
            endFrame = crawlerGroup[-1].var('frame')

            # setting up nuke
            nuke.root()['first_frame'].setValue(startFrame)
            nuke.root()['last_frame'].setValue(endFrame)

            # converting the active frame to the frame padding notation
            sourceFilePath = crawlerGroup[0].var('filePath')
            sourcePadding = crawlerGroup[0].var('padding')
            sourceExt = crawlerGroup[0].var('ext')
            sourceFilePath = '{0}{1}.{2}'.format(
                sourceFilePath[:(len(sourceExt) + sourcePadding + 1) * -1],
                "#" * sourcePadding,
                sourceExt
            )

            nuke.tcl('set sourceFile "{}"'.format(sourceFilePath))
            nuke.tcl('set targetFile "{}"'.format(self.target(crawlerGroup[0])))

            # passing all the options as tcl global variables
            for optionName in map(str, self.optionNames()):
                optionValue = self.option(optionName)

                # resolving template if necessary
                if isinstance(optionValue, basestring):
                    optionValue = self.templateOption(optionName, crawlerGroup[0])

                # adding option to as tcl variable
                nuke.tcl('set {} "{}"'.format(optionName, optionValue))

            # executing the write node
            for writeNode in nuke.allNodes('Write'):

                # skipping disabled write nodes
                if writeNode['disable'].value():
                    continue

                nuke.execute(writeNode, int(writeNode['first'].value()), int(writeNode['last'].value()))

                # multiple files (image sequence)
                currentFile = writeNode['file'].getValue()
                if "%0" in currentFile:
                    for frame in range(int(writeNode['first'].value()), int(writeNode['last'].value() + 1)):
                        bufferString = StringIO()
                        bufferString.write(currentFile % frame)

                        createdFiles.append(bufferString.getvalue())

                # single file
                else:
                    createdFiles.append(currentFile)

        return list(map(FsCrawler.createFromPath, createdFiles))


# registering task
Task.register(
    'nukeScene',
    NukeSceneTask
)

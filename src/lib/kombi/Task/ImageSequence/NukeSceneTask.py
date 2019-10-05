import os
from ..Task import Task
from ...Crawler import Crawler
from ...Crawler.Fs import FsCrawler
from ...Crawler.Fs.Image import ImageCrawler

# compatibility with python 2/3
try:
    from StringIO import StringIO  # python 2
except ImportError:
    from io import StringIO  # python 3
    basestring = str

class NukeSceneTask(Task):
    r"""
    Executes a nuke script by triggering the write nodes.

    Required options:
        scene (full path of the nuke script)

    All options with the prefix "_" defined in this task are resolved
    (in case the value contains a template string) then assigned to global tcl
    variables and to knobs under the root node in nuke. Therefore, you can use
    them drive the behavior of your template script during nuke's execution.

    Time:
    Start and end frame of the root node are automatically update with the source image
    sequence first and end frames before rendering (root.first_frame, root.last_frame).

    Tcl variables:
    Since the task options named with the prefix "_" are available inside nuke,
    it can be easily used in expressions, for instance the file path knob:
    /a/$_myOptionName/c

    $_sourceFile and $_targetFile are automatically provided as variables as well.

    Kombi knobs:
    This task creates a knob for each option named with the prefix "_" automatically
    under the root node. These knobs are created with option name. The value of
    these are always updated before the rendering. Therefore, you can create
    knobs following the naming convention beforehand then letting you
    use those knobs to drive your template nuke script (with this method you
    you can have a template script that actually displays data in the place
    holder nodes).
    [value root._sourceFile]
    [value root._targetFile]

    sourceFile and targetFile are automatically provided as knobs as well.

    Troubleshooting:
    The option "exportNukeScript" can be used to "save as" the script before
    the rendering (useful for troubleshooting). In order to use it just
    specificy the full file path as the value of the option (the file does
    not get overridden).
    For instance: "/a/exported/scene.nk"

    Reference:
    Copy the script below and paste in Nuke to use as template/reference.

    set cut_paste_input [stack 0]
    version 11.2 v2
    Read {
     inputs 0
     file_type dpx
     file "\$_sourceFile"
     format "2048 1152 0 0 2048 1152 1 "
     first {{"\[value root.first_frame]"}}
     last {{"\[value root.last_frame]"}}
     origfirst {{"\[value root.first_frame]"}}
     origlast {{"\[value root.last_frame]"}}
     origset true
     name Read1
     selected true
     xpos 8
     ypos -142
    }
    Write {
     file "\$_targetFile"
     colorspace linear
     file_type exr
     create_directories true
     first {{"\[value root.first_frame]"}}
     last {{"\[value root.last_frame]"}}
     use_limit true
     name Write1
     selected true
     xpos 108
     ypos -16
    }
    """

    __dataPrefix = "_"

    def __init__(self, *args, **kwargs):
        """
        Create a nuke template task.
        """
        super(NukeSceneTask, self).__init__(*args, **kwargs)

        self.setMetadata("wrapper.name", "nuke")
        self.setMetadata("wrapper.options", {})
        self.setMetadata("dispatch.split", True)
        self.setOption("exportNukeScript", "")

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
            sourceCrawler = crawlerGroup[0]
            targetCrawler = FsCrawler.createFromPath(self.target(sourceCrawler))
            startFrame = crawlerGroup[0].var('frame')
            endFrame = crawlerGroup[-1].var('frame')

            # setting up nuke
            nuke.root()['first_frame'].setValue(startFrame)
            nuke.root()['last_frame'].setValue(endFrame)
            self.__setInternalData(sourceCrawler, targetCrawler)

            # exporting nuke script before the execution
            exportNukeScript = self.templateOption('exportNukeScript', crawlerGroup[0])
            if exportNukeScript and not os.path.exists(exportNukeScript):
                # creating directories if necessary
                try:
                    os.makedirs(os.path.dirname(exportNukeScript))
                except (IOError, OSError) as err:
                    pass

                # exporting file
                nuke.scriptSaveAs(exportNukeScript, 0)

            # executing the write node
            for writeNode in nuke.allNodes('Write'):

                # skipping disabled write nodes
                if writeNode['disable'].value():
                    continue

                # executing render
                nuke.execute(writeNode, int(writeNode['first'].value()), int(writeNode['last'].value()))

                # multiple files (image sequence)
                currentFile = writeNode['file'].evaluate()
                renderOutputCrawler = FsCrawler.createFromPath(currentFile)
                if isinstance(renderOutputCrawler, ImageCrawler) and renderOutputCrawler.isSequence():
                    currentFileSprintf = renderOutputCrawler.tag('groupSprintf')

                    for frame in range(int(writeNode['first'].value()), int(writeNode['last'].value() + 1)):
                        bufferString = StringIO()
                        bufferString.write(currentFileSprintf % frame)
                        createdFiles.append(
                            os.path.join(
                                os.path.dirname(renderOutputCrawler.var('fullPath')),
                                bufferString.getvalue()
                            )
                        )

                # single file
                else:
                    createdFiles.append(currentFile)

        return list(map(FsCrawler.createFromPath, createdFiles))

    def __setInternalData(self, sourceCrawler, targetCrawler):
        """
        Set the data task data internally as tcl expressions and knobs.
        """
        import nuke

        def __set(name, value):
            # in case the knob does not exist, creating it.
            if name not in nuke.Root().knobs():
                if isinstance(value, int):
                    targetKnob = nuke.Int_Knob(name)
                elif isinstance(value, bool):
                    targetKnob = nuke.Boolean_Knob(name)
                elif isinstance(value, float):
                    targetKnob = nuke.Double_Knob(name)
                else:
                    targetKnob = nuke.String_Knob(name)
                nuke.Root().addKnob(targetKnob)

            # replacing all escape to forward slashes
            if isinstance(value, basestring):
                value = value.replace("\\", "/")

            # updating knob value
            nuke.Root()[name].setValue(value)

            # updating tcl variable
            nuke.tcl('set {} "{}"'.format(name, value))

        # converting frame padding to the mask # digits notation
        sourceFilePath = os.path.join(
            os.path.dirname(sourceCrawler.var('fullPath')),
            sourceCrawler.tag('group')
        )

        # converting frame padding in target to the springf notoation
        targetFilePath = targetCrawler.var('fullPath')
        if isinstance(targetCrawler, ImageCrawler) and targetCrawler.isSequence():
            targetFilePath = os.path.join(
                os.path.dirname(targetCrawler.var('fullPath')),
                targetCrawler.tag('groupSprintf')
            )

        # source/target knobs
        __set('_sourceFile', sourceFilePath)
        __set('_targetFile', targetFilePath)

        # passing all the options as tcl global variables
        for optionName in filter(lambda x: x.startswith(self.__dataPrefix), self.optionNames()):
            optionValue = self.option(optionName)
            # resolving template if necessary
            if isinstance(optionValue, basestring):
                optionValue = self.templateOption(
                    optionName,
                    sourceCrawler
                )

            __set(optionName, optionValue)


# registering task
Task.register(
    'nukeScene',
    NukeSceneTask
)

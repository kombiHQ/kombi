import os
from ..External.NukeTask import NukeTask
from ..Task import Task
from ...Crawler import Crawler
from ...Crawler.Fs import FsCrawler
from ...Crawler.Fs.Image import ImageCrawler

class NukeTemplateTask(NukeTask):
    r"""
    Executes a nuke script by triggering the write nodes.

    Required options:
        script (full file path of the nuke script)

    All options with prefixing "_" defined in this task are resolved
    (in case the value contains a template string) then assigned as knobs
    under the root node in nuke. Therefore, you can use them drive the
    behavior of your template script during nuke's execution.

    Time:
    Start and end frame of the root node are automatically update with the source image
    sequence first and end frames before rendering (root.first_frame, root.last_frame).

    Kombi knobs:
    This task creates a knob for each option named with the prefix "_" automatically
    under the root node. These knobs are created with option name. The value of
    these knobs are always updated before the rendering. Therefore, you
    can create the knobs beforehand following the naming convention then using them
    with place holder data to drive your template nuke script. With this method you
    you can always display data in the template script.
    [value root._sourceFile]
    [value root._targetFile]

    Also, the _sourceFile and _targetFile are automatically provided as knobs under
    the root node.

    Troubleshooting:
    The option "exportNukeScript" can be used to "save as" the script before
    the rendering (useful for troubleshooting). In order to use it just
    specify the full file path as the value of the option (the file does
    not get overridden).
    For instance: "/a/exported/scene.nk"

    Reference:
    Copy the script below and paste in Nuke to use as template/reference.

    set cut_paste_input [stack 0]
    version 11.2 v2
    Read {
     inputs 0
     file_type dpx
     file "\[value root._sourceFile]"
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
     file "\[value root._targetFile]"
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
        super(NukeTemplateTask, self).__init__(*args, **kwargs)

        self.setMetadata("dispatch.split", True)
        self.setOption("exportNukeScript", "")
        self.setOption("beginExtraFrames", "0")
        self.setOption("endExtraFrames", "0")
        self.setOption("renderOffsetFrames", "0")
        self.setOption("group", True)

    def _beforeRender(self):
        """
        For re-implementation: Use this method to perform extra functions before render.
        """

    def _perform(self):
        """
        Perform the task.
        """
        import nuke

        crawlers = self.crawlers()

        # loading nuke script
        nuke.scriptOpen(self.templateOption('script', crawlers[0]))

        result = []
        for crawlerGroup in Crawler.group(crawlers) if self.option('group') else [self.crawlers()]:
            sourceCrawler = crawlerGroup[0]
            targetCrawler = FsCrawler.createFromPath(self.target(sourceCrawler))
            startFrame = crawlerGroup[0].var('frame') - int(self.templateOption('beginExtraFrames', crawlerGroup[0]))
            endFrame = crawlerGroup[-1].var('frame') + int(self.templateOption('endExtraFrames', crawlerGroup[0]))
            renderOffsetFrames = int(self.templateOption('renderOffsetFrames', crawlerGroup[0]))

            # setting up nuke
            nuke.root()['first_frame'].setValue(startFrame)
            nuke.root()['last_frame'].setValue(endFrame)
            self.__setInternalData(sourceCrawler, targetCrawler)

            # giving a change for third-party apis to extend this task
            self._beforeRender()

            # exporting nuke script before the execution
            exportNukeScript = self.templateOption('exportNukeScript', crawlerGroup[0])
            if exportNukeScript and not os.path.exists(exportNukeScript):
                # creating directories if necessary
                try:
                    os.makedirs(os.path.dirname(exportNukeScript))
                except (IOError, OSError):
                    pass

                # exporting file
                nuke.scriptSaveAs(exportNukeScript, 0)

            # collecting write nodes
            nukeRenderTask = Task.create('nukeRender')
            for writeNode in nuke.allNodes('Write'):

                # skipping disabled write nodes
                if writeNode['disable'].value():
                    continue

                # adding crawler to the task
                renderCrawlers = nukeRenderTask.toRenderCrawlers(
                    writeNode,
                    int(writeNode['first'].getValue()) if writeNode['use_limit'].getValue() else startFrame + renderOffsetFrames,
                    int(writeNode['last'].getValue()) if writeNode['use_limit'].getValue() else endFrame + renderOffsetFrames
                )

                # adding crawler to render task
                for renderCrawler in renderCrawlers:
                    nukeRenderTask.add(renderCrawler)

            # executing write nodes
            result += nukeRenderTask.output()

        # adding the slate description as a crawler var. So it can be used later
        if '_slateDescription' in self.optionNames():
            for resultCrawler in result:
                resultCrawler.setVar(
                    'slateDescription',
                    self.option('_slateDescription'),
                    True
                )

        return result

    def __setInternalData(self, sourceCrawler, targetCrawler):
        """
        Set the data task data internally under the root node.
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
            if isinstance(value, str):
                value = value.replace("\\", "/")

            # updating knob value
            nuke.Root()[name].setValue(value)

        # converting frame padding to the mask # digits notation
        sourceFilePath = os.path.join(
            os.path.dirname(sourceCrawler.var('fullPath')),
            sourceCrawler.tag('group')
        )

        # converting frame padding in target to the springf notation
        targetFilePath = targetCrawler.var('fullPath')
        if isinstance(targetCrawler, ImageCrawler) and targetCrawler.isSequence():
            targetFilePath = os.path.join(
                os.path.dirname(targetCrawler.var('fullPath')),
                targetCrawler.tag('groupSprintf')
            )

        # source/target knobs
        __set('{}sourceFile'.format(self.__dataPrefix), sourceFilePath)
        __set('{}targetFile'.format(self.__dataPrefix), targetFilePath)

        # providing all options with the prefix "_" to knobs under the root node
        for optionName in filter(lambda x: x.startswith(self.__dataPrefix), self.optionNames()):
            optionValue = self.option(optionName)
            # resolving template if necessary
            if isinstance(optionValue, str) and optionName != '_slateDescription':
                optionValue = self.templateOption(
                    optionName,
                    sourceCrawler
                )

            __set(optionName, optionValue)


# registering task
Task.register(
    'nukeTemplate',
    NukeTemplateTask
)

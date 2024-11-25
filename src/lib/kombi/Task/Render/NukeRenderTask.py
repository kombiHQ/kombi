import os
import sys
from io import StringIO
from ..External.NukeTask import NukeTask
from ...Element import Element
from ...Element.Fs import FsElement
from ...Element.Fs.Image import ImageElement

class NukeRenderTask(NukeTask):
    """
    Render the write nodes in nuke.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a nuke render task.
        """
        super(NukeRenderTask, self).__init__(*args, **kwargs)

        self.setMetadata("match.types", ('hashmap',))
        self.setMetadata(
            "match.vars", {
                'dataLayout': "nukeRender"
            }
        )
        self.setMetadata("dispatch.split", True)
        self.setOption("script", "")

    @classmethod
    def toRenderElements(cls, writeNode, startFrame=None, endFrame=None):
        """
        Return hashmap elements containing the write node information used by this task.

        TODO: we want to have a specific application types to describe this information
        """
        assert writeNode.Class() == "Write", "Invalid write node type: {}".format(writeNode.fullName())

        startFrame = int(startFrame if startFrame is not None else writeNode['first'].getValue())
        endFrame = int(endFrame if endFrame is not None else writeNode['last'].getValue())

        result = []
        currentFile = writeNode['file'].evaluate()
        renderOutputElement = FsElement.createFromPath(currentFile)
        if isinstance(renderOutputElement, ImageElement) and renderOutputElement.isSequence():
            for i in range(startFrame, endFrame + 1):
                result.append(cls.__renderHashmapElement(writeNode, i, i))
        else:
            result.append(cls.__renderHashmapElement(writeNode, startFrame, endFrame))

        return result

    def __onAfterFrameRender(self):
        """
        Callback execute after every frame to update the progress.
        """
        self.__renderedFrames += 1.0

        sys.stdout.write(
            "\nALF_PROGRESS {}%\n".format(
                int((self.__renderedFrames / self.__totalFrames) * 100.0)
            )
        )
        sys.stdout.flush()

    def _perform(self):
        """
        Perform the task.
        """
        import nuke

        elements = self.elements()
        self.__totalFrames = 0
        self.__renderedFrames = 0
        nuke.addAfterFrameRender(self.__onAfterFrameRender)

        # loading nuke script
        script = self.templateOption('script', elements[0])
        if os.path.exists(script):
            nuke.scriptOpen(script)

        createdFiles = []
        for elementGroup in Element.group(elements):
            startFrame = elementGroup[0]['startFrame']
            endFrame = elementGroup[-1]['endFrame']
            self.__totalFrames += (endFrame - startFrame) + 1
            writeNode = nuke.toNode(elementGroup[0]['name'])

            if not writeNode:
                raise Exception('Could not find write node: {}'.format(elementGroup[0]['name']))

            # creating render directory if necessary
            currentFile = writeNode['file'].evaluate()
            try:
                os.makedirs(os.path.dirname(currentFile))
            except (IOError, OSError):
                pass

            # executing render
            nuke.execute(writeNode, startFrame, endFrame)

            renderOutputElement = FsElement.createFromPath(currentFile)
            if isinstance(renderOutputElement, ImageElement) and renderOutputElement.isSequence():
                currentFileSprintf = renderOutputElement.tag('groupSprintf')

                for frame in range(startFrame, endFrame + 1):
                    bufferString = StringIO()
                    bufferString.write(currentFileSprintf % frame)
                    createdFiles.append(
                        os.path.join(
                            os.path.dirname(renderOutputElement.var('fullPath')),
                            bufferString.getvalue()
                        )
                    )

            # single file
            else:
                createdFiles.append(currentFile)

        return list(map(FsElement.createFromPath, createdFiles))

    @classmethod
    def __renderHashmapElement(cls, writeNode, startFrame, endFrame):
        """
        Return a hashmap element for the input write node start and end frame.
        """
        hashmapElement = Element.create(
            {
                'name': writeNode.fullName(),
                'type': 'sequence',
                'startFrame': startFrame,
                'endFrame': endFrame,
            }
        )
        hashmapElement.setVar('dataLayout', 'nukeRender')
        hashmapElement.setTag('group', writeNode.fullName())
        hashmapElement.setVar(
            'fullPath',
            '{} {}-{}'.format(
                writeNode.fullName(),
                str(startFrame).zfill(10),
                str(endFrame).zfill(10)
            )
        )

        return hashmapElement


# registering task
NukeTask.register(
    'nukeRender',
    NukeRenderTask
)

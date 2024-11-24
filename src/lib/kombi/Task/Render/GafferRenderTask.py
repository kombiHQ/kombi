import sys
from ..External.GafferTask import GafferTask
from ...InfoCrate import InfoCrate

class GafferRenderTask(GafferTask):
    """
    Render the task nodes in gaffer.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a gaffer render task.
        """
        super(GafferRenderTask, self).__init__(*args, **kwargs)

        self.setMetadata('match.types', ('hashmap',))
        self.setMetadata(
            'match.vars', {
                'dataLayout': 'gafferRender'
            }
        )
        self.setMetadata('dispatch.split', True)
        self.setOption('script', '')

        # should be defined as a dict containing as key the name of the switch and
        # the value used to switch to
        self.setOption('switchBeforeRender', {})

    @classmethod
    def toRenderInfoCrates(cls, gafferTask, script, startFrame=None, endFrame=None):
        """
        Return hashmap infoCrates containing the write node information used by this task.

        TODO: we want to have a specific application types to describe this information (gafferNodeInfoCrate)
        """
        import Gaffer
        import GafferDispatch
        import GafferImage

        try:
            import GafferCycles
        except ImportError:
            GafferCycles = None

        try:
            import GafferArnold
        except ImportError:
            GafferArnold = None

        # checking gaffer task node
        assert isinstance(gafferTask, GafferDispatch.TaskNode), "Invalid gaffer task node!"

        # also the script node
        assert isinstance(script, Gaffer.ScriptNode), "Invalid gaffer script node!"

        # gaffer global script variable
        startFrame = startFrame if startFrame is not None else script['frameRange']['start'].getValue()
        endFrame = endFrame if endFrame is not None else script['frameRange']['end'].getValue()

        result = []
        if isinstance(gafferTask, GafferImage.ImageWriter) or \
                GafferCycles is not None and isinstance(gafferTask, GafferCycles.CyclesRender) or \
                GafferArnold is not None and isinstance(gafferTask, GafferArnold.ArnoldRender):
            for i in range(startFrame, endFrame + 1):
                result.append(cls.__renderHashmapInfoCrate(gafferTask, i, i))
        else:
            result.append(cls.__renderHashmapInfoCrate(gafferTask, startFrame, endFrame))

        return result

    def _perform(self):
        """
        Perform the task.
        """
        import Gaffer
        import GafferScene
        import GafferDispatch
        infoCrates = self.infoCrates()

        # loading gaffer scene
        script = Gaffer.ScriptNode()
        script['fileName'].setValue(self.templateOption('scene', infoCrates[0]))
        script.load()

        # switching
        for switchName, switchValue in self.templateOption('switchBeforeRender', infoCrates[0]).items():
            sys.stdout.write('Switching {} to {}\n'.format(switchName, switchValue))
            sys.stdout.flush()
            script.getChild(str(switchName))['index'].setValue(int(switchValue))

        nodes = script.children(GafferDispatch.TaskNode)
        for infoCrateGroup in InfoCrate.group(infoCrates):
            taskNodeName = infoCrateGroup[0]['name']
            startFrame = infoCrateGroup[0]['startFrame']
            endFrame = infoCrateGroup[-1]['endFrame']

            script['frameRange']['start'].setValue(startFrame)
            script['frameRange']['end'].setValue(endFrame)

            # adding context variables and executing task nodes
            with Gaffer.Context(script.context()) as context:

                for frame in range(startFrame, endFrame + 1):
                    context.setFrame(frame)

                    foundNode = False
                    for node in nodes:
                        if taskNodeName == node.getName():
                            # disabling crop window
                            for standardOptions in self.collectAncestors(node, GafferScene.StandardOptions):
                                standardOptions['options']['renderCropWindow']['enabled'].setValue(False)

                            # rendering
                            node['task'].execute()
                            foundNode = True
                            break

                    assert foundNode, "Could not find task node: {}".format(
                        taskNodeName
                    )

        return self.infoCrates()

    @classmethod
    def __renderHashmapInfoCrate(cls, gafferTask, startFrame, endFrame):
        """
        Return a hashmap infoCrate for the input write node start and end frame.
        """
        hashmapInfoCrate = InfoCrate.create(
            {
                'name': gafferTask.getName(),
                'startFrame': startFrame,
                'endFrame': endFrame,
            }
        )
        hashmapInfoCrate.setVar('dataLayout', 'gafferRender')
        hashmapInfoCrate.setVar('baseName', gafferTask.getName())
        hashmapInfoCrate.setTag('group', gafferTask.getName())
        hashmapInfoCrate.setVar('startFrame', str(startFrame).zfill(10))
        hashmapInfoCrate.setVar('endFrame', str(endFrame).zfill(10))

        hashmapInfoCrate.setVar(
            'fullPath',
            '{} {}-{}'.format(
                gafferTask.getName(),
                str(startFrame).zfill(10),
                str(endFrame).zfill(10)
            )
        )

        return hashmapInfoCrate


# registering task
GafferTask.register(
    'gafferRender',
    GafferRenderTask
)

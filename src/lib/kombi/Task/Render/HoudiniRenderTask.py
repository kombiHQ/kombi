import os
from ...InfoCrate import InfoCrate
from ..External.HoudiniTask import HoudiniTask

class HoudiniRenderTask(HoudiniTask):
    """
    Render the task nodes in houdini.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a houdini render task.
        """
        super(HoudiniRenderTask, self).__init__(*args, **kwargs)

        self.setMetadata('match.types', ('hashmap',))
        self.setMetadata(
            'match.vars', {
                'dataLayout': 'houdiniRender'
            }
        )
        self.setMetadata('dispatch.split', True)
        self.setMetadata('dispatch.splitSize', 1)
        self.setMetadata('dispatch.renderFarm.pool', 'houdini')

    @classmethod
    def toRenderInfoCrates(cls, houdiniScenePath, ropNodes, startFrame=None, endFrame=None):
        """
        Return hashmap infoCrates containing the write node information used by this task.
        """
        import hou

        result = []
        startFrame = startFrame if startFrame is not None else int(hou.expandString("$RFSTART"))
        endFrame = endFrame if endFrame is not None else int(hou.expandString("$RFEND"))
        for ropNode in ropNodes:
            assert isinstance(ropNode, hou.RopNode), "Invalid Rop node instance!"

            outputPath = ''
            # redshift
            if ropNode.type().name() == 'Redshift_ROP':
                if ropNode.parm('RS_archive_enable').eval():
                    outputPath = ropNode.parm('RS_archive_file').eval()
                else:
                    outputPath = ropNode.parm('RS_outputFileNamePrefix').eval()
                    aovSuffix = ropNode.parm('RS_outputBeautyAOVSuffix').eval()

                    if aovSuffix:
                        outputPath = os.path.join(outputPath, aovSuffix)
            elif ropNode.type().name() == 'Redshift_Proxy_Output':
                outputPath = ropNode.parm('RS_archive_file').eval()

            # mantra / hair card textures
            elif ropNode.type().name() in ('ifd', 'haircardtex'):
                outputPath = ropNode.parm('vm_picture').eval()

            # arnold
            elif ropNode.type().name() == 'arnold':
                outputPath = ropNode.parm('ar_picture').eval()

            # alembic
            elif ropNode.type().name() == 'alembic':
                outputPath = ropNode.parm('filename').eval()

            # geometry (cloth)
            elif ropNode.type().name() == 'geometry':
                outputPath = ropNode.parm('sopoutput').eval()

            # agent
            elif ropNode.type().name() == 'agent':
                outputPath = ropNode.parm('cachedir').eval()

            # rib
            elif ropNode.type().name() == 'rib':
                outputPath = ropNode.parm('ri_display').eval()

            # opengl
            elif ropNode.type().name() == 'opengl':
                outputPath = ropNode.parm('picture').eval()

            for i in range(startFrame, endFrame + 1):
                result.append(
                    cls.__renderHashmapInfoCrate(
                        houdiniScenePath,
                        ropNode.path(),
                        i,
                        i,
                        outputPath
                    )
                )

        return result

    def _perform(self):
        """
        Perform the task.
        """
        import hou

        infoCrates = self.infoCrates()
        for infoCrateGroup in InfoCrate.group(infoCrates):
            startFrame = infoCrateGroup[0]['startFrame']
            endFrame = infoCrateGroup[-1]['endFrame']
            houdiniRopName = infoCrateGroup[0].var('rop')
            scenePath = infoCrateGroup[0].var('fullPathScene')

            hou.hipFile.load(scenePath, ignore_load_warnings=True)
            print("Rendering: ", scenePath, "Rop:", houdiniRopName)
            ropNode = hou.node(houdiniRopName)

            # Render the output driver.
            ropNode.render(
                frame_range=[
                    float(startFrame),
                    float(endFrame)
                ],
                output_progress=True,
                verbose=True
            )

        return self.infoCrates()

    @classmethod
    def __renderHashmapInfoCrate(cls, houdiniScenePath, ropNodeName, startFrame, endFrame, output=''):
        """
        Return a hashmap infoCrate for the input write node start and end frame.
        """
        # todo: we dont want to depend in houdini
        sceneBaseName = os.path.basename(houdiniScenePath)
        hashmapInfoCrate = InfoCrate.create(
            {
                'name': sceneBaseName,
                'rop': ropNodeName,
                'startFrame': startFrame,
                'endFrame': endFrame,
                'output': output
            }
        )
        hashmapInfoCrate.setVar('dataLayout', 'houdiniRender')
        hashmapInfoCrate.setVar('baseName', sceneBaseName)
        hashmapInfoCrate.setVar('rop', ropNodeName)
        hashmapInfoCrate.setVar('fullPathScene', houdiniScenePath)
        hashmapInfoCrate.setTag('group', "{}-{}".format(
            sceneBaseName, ropNodeName)
        )
        hashmapInfoCrate.setVar('startFrame', str(startFrame).zfill(10))
        hashmapInfoCrate.setVar('endFrame', str(endFrame).zfill(10))

        hashmapInfoCrate.setVar(
            'fullPath',
            '{} ({}) {}-{}'.format(
                houdiniScenePath,
                ropNodeName,
                str(startFrame).zfill(10),
                str(endFrame).zfill(10)
            )
        )

        return hashmapInfoCrate


# registering task
HoudiniTask.register(
    'houdiniRender',
    HoudiniRenderTask
)

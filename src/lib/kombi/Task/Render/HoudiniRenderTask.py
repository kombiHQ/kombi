import os
from ...Crawler import Crawler
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
    def toRenderCrawlers(cls, houdiniScenePath, ropNodes, startFrame=None, endFrame=None):
        """
        Return hashmap crawlers containing the write node information used by this task.
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
                    cls.__renderHashmapCrawler(
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

        crawlers = self.crawlers()
        for crawlerGroup in Crawler.group(crawlers):
            startFrame = crawlerGroup[0]['startFrame']
            endFrame = crawlerGroup[-1]['endFrame']
            houdiniRopName = crawlerGroup[0].var('rop')
            scenePath = crawlerGroup[0].var('fullPathScene')

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

        return self.crawlers()

    @classmethod
    def __renderHashmapCrawler(cls, houdiniScenePath, ropNodeName, startFrame, endFrame, output=''):
        """
        Return a hashmap crawler for the input write node start and end frame.
        """
        # todo: we dont want to depend in houdini
        sceneBaseName = os.path.basename(houdiniScenePath)
        hashmapCrawler = Crawler.create(
            {
                'name': sceneBaseName,
                'rop': ropNodeName,
                'startFrame': startFrame,
                'endFrame': endFrame,
                'output': output
            }
        )
        hashmapCrawler.setVar('dataLayout', 'houdiniRender')
        hashmapCrawler.setVar('baseName', sceneBaseName)
        hashmapCrawler.setVar('rop', ropNodeName)
        hashmapCrawler.setVar('fullPathScene', houdiniScenePath)
        hashmapCrawler.setTag('group', "{}-{}".format(
            sceneBaseName, ropNodeName)
        )
        hashmapCrawler.setVar('startFrame', str(startFrame).zfill(10))
        hashmapCrawler.setVar('endFrame', str(endFrame).zfill(10))

        hashmapCrawler.setVar(
            'fullPath',
            '{} ({}) {}-{}'.format(
                houdiniScenePath,
                ropNodeName,
                str(startFrame).zfill(10),
                str(endFrame).zfill(10)
            )
        )

        return hashmapCrawler


# registering task
HoudiniTask.register(
    'houdiniRender',
    HoudiniRenderTask
)

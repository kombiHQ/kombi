import os
import re
import json
import time
from glob import glob
from ..Task import Task, TaskError, TaskValidationError
from ..External.GafferTask import GafferTask
from ...Crawler import Crawler
from ...Crawler.Fs.FsCrawler import FsCrawler

class GafferLoadTaskError(TaskError):
    """
    Base load gaffer load error.
    """

class GafferLoadTask(Task):
    """
    Generic gaffer to load data to gaffer.
    """

    currentScriptNode = None

    loadTypes = (
        'lookdevbox',
        'lightrigbox',
        'rendertemplatebox',
        'gaffertemplate',
        'atomsagent',
        'atomscrowdcache',
        'camera',
        'plate',
        'geo',
        'animgeocache',
        'pointCache',
        'texture',
        'volume'
    )

    def __init__(self, *args, **kwargs):
        """
        Create a gaffer load task object.
        """
        super(GafferLoadTask, self).__init__(*args, **kwargs)

        # scene containing the box nodes
        self.setOption('version', '')

        self.setMetadata(
            'ui.options.description',
            {
                'main': True,
                'visual': 'longText'
            }
        )

        # task input type
        self.setMetadata(
            'match.vars', {
                'dataLayout': [
                    'gafferLoad'
                ]
            }
        )

    def updateInfo(self, crawlers):
        """
        Return a text output displayed in the info area of the crawler.
        """
        outputPath = crawlers[0].var('fullPath')
        version = self.option('version')

        jsonInfoFilePath = os.path.join(outputPath, version, 'info.json')
        jsonContents = {}
        if os.path.exists(jsonInfoFilePath):
            with open(jsonInfoFilePath) as f:
                jsonContents = json.load(f)

            jsonContents['createdTime'] = time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.strptime(time.ctime(os.path.getctime(jsonInfoFilePath)))
            )

        output = []
        for key, value in jsonContents.items():
            output.append("{}: {}".format(self.__camelCaseToSpaced(key), value))

        return '\n'.join(output)

    def setup(self, crawlers):
        """
        Setting the initial value for output dir.
        """
        crawler = crawlers[0]

        versions = set()
        if os.path.exists(crawler.var('fullPath')):
            for node in os.listdir(crawler.var('fullPath')):
                if os.path.isdir(os.path.join(crawler.var('fullPath'), node)) and node.startswith('v') and node[1:].isdigit():
                    versions.add(node)

        allVersions = sorted(list(versions), reverse=True)

        self.setMetadata(
            'ui.options.version',
            {
                'main': True,
                'visual': 'presets',
                'presets': allVersions,
            }
        )

        self.setOption('version', allVersions[0] if allVersions else '')

    def validate(self, crawlers=None):
        """
        Validating then updating crawler information with the new output dir.
        """
        if not crawlers:
            return

        for crawler in crawlers:
            if not self.option('version'):
                raise TaskValidationError(
                    'Version cannot be empty!'
                )
            elif not os.path.exists(os.path.join(crawler.var('fullPath'), self.option('version'))):
                raise TaskValidationError(
                    'Version does not exist!'
                )

    def _perform(self):
        """
        Perform the task.
        """
        import Gaffer
        import GafferScene
        import GafferArnold
        import GafferImage
        import AtomsGaffer

        scriptNode = GafferLoadTask.currentScriptNode()
        result = []
        for crawler in self.crawlers():
            dataDirectory = os.path.join(crawler.var('outputDir'), crawler.var('outputType'), crawler.var('outputName'), self.templateOption('version', crawler), 'd')
            outputType = crawler.var('outputType')

            if outputType.endswith('box'):
                referenceFilePaths = list(glob('{}/*.gfr'.format(dataDirectory)))

                if not referenceFilePaths:
                    raise GafferLoadTaskError('Version is broken, missing data: {}'.format(dataDirectory))

                for referenceFilePath in referenceFilePaths:
                    referenceNode = Gaffer.Reference('{}_{}'.format(crawler.var('outputName').replace('-', '_'), crawler.var('outputType')[:-3]))
                    scriptNode.addChild(referenceNode)
                    referenceNode.load(referenceFilePath)
                    scriptNode.selection().add(referenceNode)

                    result.append(FsCrawler.createFromPath(referenceFilePath))

            elif outputType in ('geo', 'animgeocache', 'pointCache'):
                geoFilePaths = list(glob('{}/*.abc'.format(dataDirectory)))
                if not geoFilePaths:
                    continue
                geoScene = GafferScene.SceneReader('{}_{}'.format(crawler.var('outputName').replace('-', '_'), crawler.var('outputType')))
                scriptNode.addChild(geoScene)
                geoScene['fileName'].setValue(str(geoFilePaths[0]))
                scriptNode.selection().add(geoScene)

            elif outputType == 'plate':
                platePaths = list(sorted(glob('{}/exr/*.exr'.format(dataDirectory))))
                if not platePaths:
                    continue

                # adding the frame padding
                platePath = platePaths[0].split('.')
                platePath[-2] = '####'
                platePath = '.'.join(platePath)

                # setting frame range
                startFrame = int(platePaths[0].split('.')[-2])
                endFrame = int(platePaths[-1].split('.')[-2])
                scriptNode['frameRange']['start'].setValue(startFrame)
                scriptNode['frameRange']['end'].setValue(endFrame)
                scriptNode['frame'].setValue(float(startFrame))

                # loading plate
                imageReader = GafferImage.ImageReader('{}_{}'.format(crawler.var('outputName').replace('-', '_'), crawler.var('outputType')))
                scriptNode.addChild(imageReader)
                imageReader['fileName'].setValue(str(platePath))
                scriptNode.selection().add(imageReader)

            elif outputType == 'camera':
                cameraFilePaths = list(glob('{}/*.usd'.format(dataDirectory)))
                if not cameraFilePaths:
                    continue
                geoScene = GafferScene.SceneReader('{}_{}'.format(crawler.var('outputName').replace('-', '_'), crawler.var('outputType')))
                scriptNode.addChild(geoScene)
                geoScene['fileName'].setValue(str(cameraFilePaths[0]))
                scriptNode.selection().add(geoScene)

            elif outputType == 'volume':
                vdbFilePaths = list(glob('{}/*.vdb'.format(dataDirectory)))
                if not vdbFilePaths:
                    continue

                vdbFilePathParts = vdbFilePaths[0].split('.')
                vdbFilePathParts[-2] = "#" * len(vdbFilePathParts[-2])

                volumeScene = GafferScene.SceneReader('{}_{}'.format(crawler.var('outputName').replace('-', '_'), crawler.var('outputType')))
                scriptNode.addChild(volumeScene)
                volumeScene['fileName'].setValue('.'.join(vdbFilePathParts))
                scriptNode.selection().add(volumeScene)

            elif outputType == 'gaffertemplate':
                gafferFilePaths = list(glob('{}/*.gfr'.format(dataDirectory)))
                if not gafferFilePaths:
                    continue

                node = Gaffer.ScriptNode()
                node['fileName'].setValue(str(gafferFilePaths[0]))
                node.load()

                scriptNode.copy(node)
                scriptNode.paste(scriptNode)

            elif outputType == 'atomsagent':
                agentVariationPath = os.path.join(dataDirectory, 'variation.json')
                if not os.path.exists(agentVariationPath):
                    continue
                atomsVariationReader = AtomsGaffer.AtomsVariationReader('{}_variation'.format(crawler.var('outputName').replace('-', '_').replace('.', '_')))
                scriptNode.addChild(atomsVariationReader)
                atomsVariationReader['atomsVariationFile'].setValue(str(agentVariationPath))
                scriptNode.selection().add(atomsVariationReader)

            elif outputType == 'atomscrowdcache':
                crowdCachePath = os.path.join(dataDirectory, 'd.atoms')
                if not os.path.exists(crowdCachePath):
                    continue
                atomsCrowdReader = AtomsGaffer.AtomsCrowdReader('{}_crowd'.format(crawler.var('outputName').replace('-', '_').replace('.', '_')))
                scriptNode.addChild(atomsCrowdReader)
                atomsCrowdReader['atomsSimFile'].setValue(str(crowdCachePath))
                scriptNode.selection().add(atomsCrowdReader)

            elif outputType == 'texture':
                textureFilePaths = list(glob('{}/tx/*.tx'.format(dataDirectory)))
                if not textureFilePaths:
                    continue

                alreadyCreated = []
                for textureFilePath in textureFilePaths:
                    textureBaseName = os.path.basename(textureFilePath)
                    textureParts = textureBaseName.split('.')
                    if textureParts[-2].isdigit():
                        textureParts[-2] = '<UDIM>'

                    normalizedBaseName = '.'.join(textureParts)
                    if normalizedBaseName in alreadyCreated:
                        continue

                    alreadyCreated.append(normalizedBaseName)

                    textureShader = GafferArnold.ArnoldShader('{}_{}'.format(crawler.var('outputName'), '.'.join(textureParts[:-2])).replace('-', '_'))
                    textureShader.loadShader("image")
                    scriptNode.addChild(textureShader)
                    textureShader['parameters']['filename'].setValue(str(os.path.join(os.path.dirname(textureFilePath), normalizedBaseName)))
                    scriptNode.selection().add(textureShader)

        return result

    @classmethod
    def toLoadCrawler(cls, outputName, outputType, outputDir, loaded=False):
        """
        Return a hashmap crawler for the load gaffer data.
        """
        hashmapCrawler = Crawler.create(
            {
                'name': outputName
            }
        )

        hashmapCrawler.setVar('dataLayout', 'gafferLoad')
        hashmapCrawler.setVar('baseName', os.path.join(outputType, outputName))
        hashmapCrawler.setVar('outputName', outputName)
        hashmapCrawler.setVar('loaded', 'Loaded' if loaded else ' ')
        hashmapCrawler.setVar('outputVersion', '')
        hashmapCrawler.setVar('outputDir', outputDir)
        hashmapCrawler.setVar('location', os.path.dirname(outputDir))
        hashmapCrawler.setVar('outputType', outputType)

        hashmapCrawler.setVar(
            'fullPath',
            os.path.join(outputDir, outputType, outputName)
        )

        return hashmapCrawler

    @classmethod
    def __camelCaseToSpaced(cls, text):
        """
        Return the input camelCase string to spaced.
        """
        return text[0].upper() + re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>", text[1:])


# registering task
GafferTask.register(
    'gafferLoad',
    GafferLoadTask
)

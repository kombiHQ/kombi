import os
from glob import glob
from ..Task import Task, TaskError, TaskValidationError
from ..External.GafferTask import GafferTask
from ...Element import Element
from ...Element.Fs.FsElement import FsElement

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

    def setup(self, elements):
        """
        Setting the initial value for output dir.
        """
        element = elements[0]

        versions = set()
        if os.path.exists(element.var('fullPath')):
            for node in os.listdir(element.var('fullPath')):
                if os.path.isdir(os.path.join(element.var('fullPath'), node)) and node.startswith('v') and node[1:].isdigit():
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
        self.setMetadata('task.options.version.template', True)

    def validate(self, elements=None):
        """
        Validating then updating element information with the new output dir.
        """
        if not elements:
            return

        for element in elements:
            if not self.option('version'):
                raise TaskValidationError(
                    'Version cannot be empty!'
                )
            elif not os.path.exists(os.path.join(element.var('fullPath'), self.option('version'))):
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
        for element in self.elements():
            dataDirectory = os.path.join(element.var('outputDir'), element.var('outputType'), element.var('outputName'), self.option('version', element), 'd')
            outputType = element.var('outputType')

            if outputType.endswith('box'):
                referenceFilePaths = list(glob('{}/*.gfr'.format(dataDirectory)))

                if not referenceFilePaths:
                    raise GafferLoadTaskError('Version is broken, missing data: {}'.format(dataDirectory))

                for referenceFilePath in referenceFilePaths:
                    referenceNode = Gaffer.Reference('{}_{}'.format(element.var('outputName').replace('-', '_'), element.var('outputType')[:-3]))
                    scriptNode.addChild(referenceNode)
                    referenceNode.load(referenceFilePath)
                    scriptNode.selection().add(referenceNode)

                    result.append(FsElement.createFromPath(referenceFilePath))

            elif outputType in ('geo', 'animgeocache', 'pointCache'):
                geoFilePaths = list(glob('{}/*.abc'.format(dataDirectory)))
                if not geoFilePaths:
                    continue
                geoScene = GafferScene.SceneReader('{}_{}'.format(element.var('outputName').replace('-', '_'), element.var('outputType')))
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
                imageReader = GafferImage.ImageReader('{}_{}'.format(element.var('outputName').replace('-', '_'), element.var('outputType')))
                scriptNode.addChild(imageReader)
                imageReader['fileName'].setValue(str(platePath))
                scriptNode.selection().add(imageReader)

            elif outputType == 'camera':
                cameraFilePaths = list(glob('{}/*.usd'.format(dataDirectory)))
                if not cameraFilePaths:
                    continue
                geoScene = GafferScene.SceneReader('{}_{}'.format(element.var('outputName').replace('-', '_'), element.var('outputType')))
                scriptNode.addChild(geoScene)
                geoScene['fileName'].setValue(str(cameraFilePaths[0]))
                scriptNode.selection().add(geoScene)

            elif outputType == 'volume':
                vdbFilePaths = list(glob('{}/*.vdb'.format(dataDirectory)))
                if not vdbFilePaths:
                    continue

                vdbFilePathParts = vdbFilePaths[0].split('.')
                vdbFilePathParts[-2] = "#" * len(vdbFilePathParts[-2])

                volumeScene = GafferScene.SceneReader('{}_{}'.format(element.var('outputName').replace('-', '_'), element.var('outputType')))
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
                atomsVariationReader = AtomsGaffer.AtomsVariationReader('{}_variation'.format(element.var('outputName').replace('-', '_').replace('.', '_')))
                scriptNode.addChild(atomsVariationReader)
                atomsVariationReader['atomsVariationFile'].setValue(str(agentVariationPath))
                scriptNode.selection().add(atomsVariationReader)

            elif outputType == 'atomscrowdcache':
                crowdCachePath = os.path.join(dataDirectory, 'd.atoms')
                if not os.path.exists(crowdCachePath):
                    continue
                atomsCrowdReader = AtomsGaffer.AtomsCrowdReader('{}_crowd'.format(element.var('outputName').replace('-', '_').replace('.', '_')))
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

                    textureShader = GafferArnold.ArnoldShader('{}_{}'.format(element.var('outputName'), '.'.join(textureParts[:-2])).replace('-', '_'))
                    textureShader.loadShader("image")
                    scriptNode.addChild(textureShader)
                    textureShader['parameters']['filename'].setValue(str(os.path.join(os.path.dirname(textureFilePath), normalizedBaseName)))
                    scriptNode.selection().add(textureShader)

        return result

    @classmethod
    def toLoadElement(cls, outputName, outputType, outputDir, loaded=False):
        """
        Return a hashmap element for the load gaffer data.
        """
        hashmapElement = Element.create(
            {
                'name': outputName
            }
        )

        hashmapElement.setVar('dataLayout', 'gafferLoad')
        hashmapElement.setVar('baseName', os.path.join(outputType, outputName))
        hashmapElement.setVar('outputName', outputName)
        hashmapElement.setVar('loaded', 'Loaded' if loaded else ' ')
        hashmapElement.setVar('outputVersion', '')
        hashmapElement.setVar('outputDir', outputDir)
        hashmapElement.setVar('location', os.path.dirname(outputDir))
        hashmapElement.setVar('outputType', outputType)

        hashmapElement.setVar(
            'fullPath',
            os.path.join(outputDir, outputType, outputName)
        )

        return hashmapElement


# registering task
GafferTask.register(
    'gafferLoad',
    GafferLoadTask
)

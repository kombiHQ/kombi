import os
import re
import json
from ..Task import TaskError, TaskValidationError
from ..External.GafferTask import GafferTask
from ...Template import Template
from ...InfoCrate import InfoCrate
from ...InfoCrate.Fs.FsInfoCrate import FsInfoCrate

class GafferBoxExportTaskError(TaskError):
    """
    Base gaffer box export error.
    """

class GafferBoxExportTask(GafferTask):
    """
    Generic gaffer task used to export gaffer a box as reference from a scene.
    """

    referenceTypes = (
        'lookdevbox',
        'lightrigbox'
    )

    def __init__(self, *args, **kwargs):
        """
        Create a export reference task object.
        """
        super(GafferBoxExportTask, self).__init__(*args, **kwargs)

        # scene containing the box nodes
        self.setOption('scene', '')
        self.setOption('outputDir', '')
        self.setOption('description', '')
        self.setOption('info', '(parentdirname {fullPath})/info.json')
        self.setOption('infoData', {})
        self.setOption('outputRegexValidation', '')
        self.setOption('outputRegexValidationFailMessage', 'Invalid output location!')

        self.setMetadata(
            'ui.options.description',
            {
                'main': True,
                'visual': 'longText'
            }
        )

        self.setMetadata(
            'ui.options.outputDir',
            {
                'main': True,
                'visual': 'directoryPath',
                'label': 'Output Location',
                'presets': []
            }
        )

        # task input type
        self.setMetadata(
            'match.vars', {
                'dataLayout': [
                    'gafferBox'
                ]
            }
        )

    def setup(self, infoCrates):
        """
        Setting the initial value for output dir.
        """
        self.setOption(
            'outputDir',
            infoCrates[0].var('outputDir')
        )

        outputDirs = []
        currentPath = os.path.dirname(self.option('outputDir'))
        while currentPath:
            currentPath = Template('(resolvepath {basePath} output)').value({'basePath': currentPath})
            if not currentPath:
                break

            outputDirs.append(currentPath)
            currentPath = os.path.dirname(os.path.dirname(currentPath))

        self.setMetadata('ui.options.outputDir.presets', outputDirs)

    def validate(self, infoCrates=None):
        """
        Validating then updating infoCrate information with the new output dir.
        """
        if not infoCrates:
            return

        # updating infoCrates with the new output dir
        for infoCrate in infoCrates:
            infoCrate.setVar('outputDir', self.option('outputDir'))

            if not infoCrate.var('outputName'):
                raise TaskValidationError(
                    'Output name cannot be empty for {}'.format(infoCrate.var('baseName'))
                )
            elif len(self.option('description')) < 10:
                raise TaskValidationError(
                    'Description is too short. It requires at least 10 characters: {}'.format(infoCrate.var('baseName'))
                )

            elif infoCrate.var('outputName').lower() == 'box' or re.match('box[0-9]+', infoCrate.var('outputName').lower()):
                raise TaskValidationError(
                    'Invalid output name, it cannot be published using default box name: {}'.format(infoCrate.var('baseName'))
                )

            elif not re.match('^[a-zA-Z0-9-]+$', infoCrate.var('outputName')):
                raise TaskValidationError(
                    'Output name cannot contain special characters (except from dash): {}'.format(infoCrate.var('outputName'))
                )

            elif not infoCrate.var('outputType'):
                raise TaskValidationError(
                    'Reference type cannot be empty: {}'.format(infoCrate.var('baseName'))
                )

            elif infoCrate.var('outputType') not in self.referenceTypes:
                raise TaskValidationError(
                    'Invalid reference type ({}) for: {}'.format(infoCrate.var('outputType'), infoCrate.var('baseName'))
                )

            elif not infoCrate.var('outputDir'):
                raise TaskValidationError(
                    'Output location cannot be empty!'
                )
            elif not os.path.exists(infoCrate.var('outputDir')):
                raise TaskValidationError(
                    'Output location does not exist: {}'.format(infoCrate.var('outputDir'))
                )
            elif self.option('outputRegexValidation') and not re.match(self.templateOption('outputRegexValidation', infoCrate), infoCrate.var('outputDir')):
                raise TaskValidationError(
                    self.templateOption('outputRegexValidationFailMessage', infoCrate)
                )

    def _perform(self):
        """
        Perform the task.
        """
        import Gaffer

        infoCrates = self.infoCrates()
        sceneFullPath = self.templateOption('scene', infoCrates[0])

        if not os.path.exists(sceneFullPath):
            raise GafferBoxExportTaskError('Invalid Scene: {}'.format(sceneFullPath))

        # loading gaffer scene
        script = Gaffer.ScriptNode()
        script['fileName'].setValue(self.templateOption('scene', infoCrates[0]))
        script.load()

        result = []
        for index, infoCrate in enumerate(self.infoCrates()):
            targetPath = self.target(infoCrate)

            # creating directories if necessary
            os.makedirs(os.path.dirname(targetPath), exist_ok=True)

            # writing info file
            if index == 0:
                infoData = self.option('infoData')
                infoData['user'] = os.environ.get('KOMBI_USER')
                infoData['description'] = self.option('description')
                infoData['gafferVersion'] = os.environ.get('BVER_GAFFER_VERSION')
                infoData['arnoldVersion'] = os.environ.get('BVER_GAFFER_ARNOLD_VERSION')

                with open(self.templateOption('info', FsInfoCrate.createFromPath(targetPath)), 'w') as f:
                    json.dump(
                        infoData,
                        f,
                        indent=4,
                        sort_keys=True
                    )

            script.descendant(str(infoCrate.var('relativeName'))).exportForReference(targetPath)
            result.append(FsInfoCrate.createFromPath(targetPath))

        return result

    @classmethod
    def toBoxInfoCrate(cls, script, gafferBox, outputType='', outputDir=''):
        """
        Return a hashmap infoCrate for the input gaffer box.
        """
        import Gaffer

        # checking gaffer box node
        assert isinstance(gafferBox, Gaffer.Box), "Invalid gaffer box node!"

        hashmapInfoCrate = InfoCrate.create(
            {
                'name': gafferBox.getName()
            }
        )

        hashmapInfoCrate.setVar('dataLayout', 'gafferBox')
        hashmapInfoCrate.setVar('baseName', gafferBox.getName())
        hashmapInfoCrate.setVar('outputName', cls.outputName(gafferBox.getName()))
        hashmapInfoCrate.setVar('relativeName', gafferBox.relativeName(script))
        hashmapInfoCrate.setTag('outputName.allowEmpty', False)
        hashmapInfoCrate.setVar('outputDir', outputDir)
        hashmapInfoCrate.setVar('outputType', outputType or cls.outputType(gafferBox.getName()))
        hashmapInfoCrate.setTag('outputType.presets', cls.referenceTypes)
        hashmapInfoCrate.setTag('outputType.allowEmpty', False)

        hashmapInfoCrate.setVar(
            'fullPath',
            gafferBox.getName()
        )

        return hashmapInfoCrate

    @classmethod
    def outputName(cls, name):
        """
        Return a nice output name.
        """
        result = name.split('_')

        # getting rid of any reference type in the output name
        newName = []
        for resultPart in result:
            skip = False
            normalizedResultPart = resultPart.lower()
            for outputType in cls.referenceTypes:
                normalizedOutputType = outputType.lower()[:-3]
                if normalizedOutputType in normalizedResultPart:  # we don't mind about the box
                    if len(normalizedOutputType) != len(normalizedResultPart):
                        resultPart = normalizedResultPart.replace(normalizedOutputType.lower(), '')
                        normalizedResultPart = resultPart
                    else:
                        skip = True
                        break

            if skip or not resultPart:
                continue
            newName.append(resultPart)

        result = '-'.join(newName)
        return '{}{}'.format(result[0].lower(), result[1:])

    @classmethod
    def outputType(cls, name):
        """
        Return a reference type name.
        """
        for outputType in cls.referenceTypes:
            if outputType[:-3].lower() in name.lower():
                return outputType

        return ''


# registering task
GafferTask.register(
    'gafferBoxExport',
    GafferBoxExportTask
)

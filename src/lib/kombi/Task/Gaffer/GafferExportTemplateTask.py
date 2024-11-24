import os
import re
import json
from ..Task import Task, TaskError, TaskValidationError
from ...Template import Template
from ...InfoCrate import InfoCrate
from ...InfoCrate.Fs.FsInfoCrate import FsInfoCrate

class GafferExportTemplateTaskError(TaskError):
    """
    Base export template error.
    """

class GafferExportTemplateTask(Task):
    """
    Generic gaffer task used to export the selection as as a gaffer scene.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a export template task object.
        """
        super(GafferExportTemplateTask, self).__init__(*args, **kwargs)

        # scene to be exported as template
        self.setOption('scene', '')
        self.setOption('outputDir', '')
        self.setOption('outputName', '')
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

        self.setMetadata(
            'ui.options.outputName',
            {
                'main': True,
                'required': True,
                'visual': 'presets',
                'editable': True,
                'presets': []
            }
        )

        # task input type
        self.setMetadata(
            'match.vars', {
                'dataLayout': [
                    'gafferTemplate'
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

        # collecting all output names
        outputNames = set()
        for outputDir in outputDirs:
            gafferTemplateDir = os.path.join(outputDir, 'gaffertemplate')
            if not os.path.exists(gafferTemplateDir):
                continue

            for node in os.listdir(gafferTemplateDir):
                if not os.path.isdir(os.path.join(gafferTemplateDir, node)):
                    continue
                outputNames.add(node)

        self.setMetadata('ui.options.outputName.presets', list(sorted(outputNames)))

    def validate(self, infoCrates=None):
        """
        Validating then updating infoCrate information with the new output dir.
        """
        if not infoCrates:
            return

        # updating infoCrates with the new output dir
        for infoCrate in infoCrates:
            infoCrate.setVar('outputDir', self.option('outputDir'))
            infoCrate.setVar('outputName', self.option('outputName'))

            if not infoCrate.var('outputName'):
                raise TaskValidationError(
                    'Output name cannot be empty for {}'.format(infoCrate.var('baseName'))
                )
            elif len(self.option('description')) < 10:
                raise TaskValidationError(
                    'Description is too short. It requires at least 10 characters: {}'.format(infoCrate.var('baseName'))
                )
            elif not re.match('^[a-zA-Z0-9-]+$', infoCrate.var('outputName')):
                raise TaskValidationError(
                    'Output name cannot contain special characters (except from dash): {}'.format(infoCrate.var('outputName'))
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
        infoCrates = self.infoCrates()
        sceneFullPath = self.templateOption('scene', infoCrates[0])

        if not os.path.exists(sceneFullPath):
            raise GafferExportTemplateTaskError('Invalid Scene: {}'.format(sceneFullPath))

        result = []
        for index, infoCrate in enumerate(self.infoCrates()):
            targetPath = self.target(infoCrate)

            # copying file
            byteCopyTask = self.create('byteCopy')
            byteCopyTask.add(FsInfoCrate.createFromPath(sceneFullPath), targetPath)
            byteCopyTask.output()

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

            result.append(FsInfoCrate.createFromPath(targetPath))

        return result

    @classmethod
    def toTemplateInfoCrate(cls, outputDir=''):
        """
        Return a hashmap infoCrate for the input selection.
        """
        # checking gaffer box node
        hashmapInfoCrate = InfoCrate.create({})
        hashmapInfoCrate.setVar('dataLayout', 'gafferTemplate')
        hashmapInfoCrate.setVar('baseName', 'template')
        hashmapInfoCrate.setVar('outputName', '')
        hashmapInfoCrate.setTag('outputName.allowEmpty', False)
        hashmapInfoCrate.setVar('outputDir', outputDir)

        hashmapInfoCrate.setVar(
            'fullPath',
            '/template'
        )

        return hashmapInfoCrate


# registering task
Task.register(
    'gafferExportTemplate',
    GafferExportTemplateTask
)

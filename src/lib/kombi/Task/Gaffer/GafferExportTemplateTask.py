import os
import re
import json
from ..Task import Task, TaskError, TaskValidationError
from ...Template import Template
from ...Element import Element
from ...Element.Fs.FsElement import FsElement

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

    def setup(self, elements):
        """
        Setting the initial value for output dir.
        """
        self.setOption(
            'outputDir',
            elements[0].var('outputDir')
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

    def validate(self, elements=None):
        """
        Validating then updating element information with the new output dir.
        """
        if not elements:
            return

        # updating elements with the new output dir
        for element in elements:
            element.setVar('outputDir', self.option('outputDir'))
            element.setVar('outputName', self.option('outputName'))

            if not element.var('outputName'):
                raise TaskValidationError(
                    'Output name cannot be empty for {}'.format(element.var('baseName'))
                )
            elif len(self.option('description')) < 10:
                raise TaskValidationError(
                    'Description is too short. It requires at least 10 characters: {}'.format(element.var('baseName'))
                )
            elif not re.match('^[a-zA-Z0-9-]+$', element.var('outputName')):
                raise TaskValidationError(
                    'Output name cannot contain special characters (except from dash): {}'.format(element.var('outputName'))
                )
            elif not element.var('outputDir'):
                raise TaskValidationError(
                    'Output location cannot be empty!'
                )
            elif not os.path.exists(element.var('outputDir')):
                raise TaskValidationError(
                    'Output location does not exist: {}'.format(element.var('outputDir'))
                )
            elif self.option('outputRegexValidation') and not re.match(self.templateOption('outputRegexValidation', element), element.var('outputDir')):
                raise TaskValidationError(
                    self.templateOption('outputRegexValidationFailMessage', element)
                )

    def _perform(self):
        """
        Perform the task.
        """
        elements = self.elements()
        sceneFullPath = self.templateOption('scene', elements[0])

        if not os.path.exists(sceneFullPath):
            raise GafferExportTemplateTaskError('Invalid Scene: {}'.format(sceneFullPath))

        result = []
        for index, element in enumerate(self.elements()):
            targetPath = self.target(element)

            # copying file
            byteCopyTask = self.create('byteCopy')
            byteCopyTask.add(FsElement.createFromPath(sceneFullPath), targetPath)
            byteCopyTask.output()

            # writing info file
            if index == 0:
                infoData = self.option('infoData')
                infoData['user'] = os.environ.get('KOMBI_USER')
                infoData['description'] = self.option('description')
                infoData['gafferVersion'] = os.environ.get('BVER_GAFFER_VERSION')
                infoData['arnoldVersion'] = os.environ.get('BVER_GAFFER_ARNOLD_VERSION')

                with open(self.templateOption('info', FsElement.createFromPath(targetPath)), 'w') as f:
                    json.dump(
                        infoData,
                        f,
                        indent=4,
                        sort_keys=True
                    )

            result.append(FsElement.createFromPath(targetPath))

        return result

    @classmethod
    def toTemplateElement(cls, outputDir=''):
        """
        Return a hashmap element for the input selection.
        """
        # checking gaffer box node
        hashmapElement = Element.create({})
        hashmapElement.setVar('dataLayout', 'gafferTemplate')
        hashmapElement.setVar('baseName', 'template')
        hashmapElement.setVar('outputName', '')
        hashmapElement.setTag('outputName.allowEmpty', False)
        hashmapElement.setVar('outputDir', outputDir)

        hashmapElement.setVar(
            'fullPath',
            '/template'
        )

        return hashmapElement


# registering task
Task.register(
    'gafferExportTemplate',
    GafferExportTemplateTask
)

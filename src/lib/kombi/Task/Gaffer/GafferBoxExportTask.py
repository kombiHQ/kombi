import os
import re
import json
from ..Task import TaskError, TaskValidationError
from ..External.GafferTask import GafferTask
from ...Template import Template
from ...Crawler import Crawler
from ...Crawler.Fs.FsCrawler import FsCrawler

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

    def setup(self, crawlers):
        """
        Setting the initial value for output dir.
        """
        self.setOption(
            'outputDir',
            crawlers[0].var('outputDir')
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

    def validate(self, crawlers=None):
        """
        Validating then updating crawler information with the new output dir.
        """
        if not crawlers:
            return

        # updating crawlers with the new output dir
        for crawler in crawlers:
            crawler.setVar('outputDir', self.option('outputDir'))

            if not crawler.var('outputName'):
                raise TaskValidationError(
                    'Output name cannot be empty for {}'.format(crawler.var('baseName'))
                )
            elif len(self.option('description')) < 10:
                raise TaskValidationError(
                    'Description is too short. It requires at least 10 characters: {}'.format(crawler.var('baseName'))
                )

            elif crawler.var('outputName').lower() == 'box' or re.match('box[0-9]+', crawler.var('outputName').lower()):
                raise TaskValidationError(
                    'Invalid output name, it cannot be published using default box name: {}'.format(crawler.var('baseName'))
                )

            elif not re.match('^[a-zA-Z0-9-]+$', crawler.var('outputName')):
                raise TaskValidationError(
                    'Output name cannot contain special characters (except from dash): {}'.format(crawler.var('outputName'))
                )

            elif not crawler.var('outputType'):
                raise TaskValidationError(
                    'Reference type cannot be empty: {}'.format(crawler.var('baseName'))
                )

            elif crawler.var('outputType') not in self.referenceTypes:
                raise TaskValidationError(
                    'Invalid reference type ({}) for: {}'.format(crawler.var('outputType'), crawler.var('baseName'))
                )

            elif not crawler.var('outputDir'):
                raise TaskValidationError(
                    'Output location cannot be empty!'
                )
            elif not os.path.exists(crawler.var('outputDir')):
                raise TaskValidationError(
                    'Output location does not exist: {}'.format(crawler.var('outputDir'))
                )
            elif self.option('outputRegexValidation') and not re.match(self.templateOption('outputRegexValidation', crawler), crawler.var('outputDir')):
                raise TaskValidationError(
                    self.templateOption('outputRegexValidationFailMessage', crawler)
                )

    def _perform(self):
        """
        Perform the task.
        """
        import Gaffer

        crawlers = self.crawlers()
        sceneFullPath = self.templateOption('scene', crawlers[0])

        if not os.path.exists(sceneFullPath):
            raise GafferBoxExportTaskError('Invalid Scene: {}'.format(sceneFullPath))

        # loading gaffer scene
        script = Gaffer.ScriptNode()
        script['fileName'].setValue(self.templateOption('scene', crawlers[0]))
        script.load()

        result = []
        for index, crawler in enumerate(self.crawlers()):
            targetPath = self.target(crawler)

            # creating directories if necessary
            os.makedirs(os.path.dirname(targetPath), exist_ok=True)

            # writing info file
            if index == 0:
                infoData = self.option('infoData')
                infoData['user'] = os.environ.get('KOMBI_USER')
                infoData['description'] = self.option('description')
                infoData['gafferVersion'] = os.environ.get('BVER_GAFFER_VERSION')
                infoData['arnoldVersion'] = os.environ.get('BVER_GAFFER_ARNOLD_VERSION')

                with open(self.templateOption('info', FsCrawler.createFromPath(targetPath)), 'w') as f:
                    json.dump(
                        infoData,
                        f,
                        indent=4,
                        sort_keys=True
                    )

            script.descendant(str(crawler.var('relativeName'))).exportForReference(targetPath)
            result.append(FsCrawler.createFromPath(targetPath))

        return result

    @classmethod
    def toBoxCrawler(cls, script, gafferBox, outputType='', outputDir=''):
        """
        Return a hashmap crawler for the input gaffer box.
        """
        import Gaffer

        # checking gaffer box node
        assert isinstance(gafferBox, Gaffer.Box), "Invalid gaffer box node!"

        hashmapCrawler = Crawler.create(
            {
                'name': gafferBox.getName()
            }
        )

        hashmapCrawler.setVar('dataLayout', 'gafferBox')
        hashmapCrawler.setVar('baseName', gafferBox.getName())
        hashmapCrawler.setVar('outputName', cls.outputName(gafferBox.getName()))
        hashmapCrawler.setVar('relativeName', gafferBox.relativeName(script))
        hashmapCrawler.setTag('outputName.allowEmpty', False)
        hashmapCrawler.setVar('outputDir', outputDir)
        hashmapCrawler.setVar('outputType', outputType or cls.outputType(gafferBox.getName()))
        hashmapCrawler.setTag('outputType.presets', cls.referenceTypes)
        hashmapCrawler.setTag('outputType.allowEmpty', False)

        hashmapCrawler.setVar(
            'fullPath',
            gafferBox.getName()
        )

        return hashmapCrawler

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

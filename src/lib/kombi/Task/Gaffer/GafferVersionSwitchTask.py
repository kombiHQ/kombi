import os
import re
import json
import sys
import time
import traceback
from ..Task import Task, TaskError, TaskValidationError
from ..External.GafferTask import GafferTask
from ...Template import Template
from ...Crawler import Crawler

class GafferSwitchVersionTaskError(TaskError):
    """
    Base switch version error.
    """

class GafferVersionSwitchTask(Task):
    """
    Generic gaffer task used to switch all node versions in gaffer.
    """

    currentScriptNode = None
    __filePathWidgetTypes = (
        'GafferUI.FileSystemPathPlugValueWidget',
        'GafferUI.PathPlugValueWidget'
    )

    def __init__(self, *args, **kwargs):
        """
        Create a load reference task object.
        """
        super(GafferVersionSwitchTask, self).__init__(*args, **kwargs)

        # scene containing the box nodes
        self.setOption('version', '')

        # task input type
        self.setMetadata(
            'match.vars', {
                'dataLayout': [
                    'gafferVersionSwitch'
                ]
            }
        )

    def switchInfo(self, crawlers):
        """
        Return a text output displayed in the info area of the crawler.
        """
        versionsPath = crawlers[0].var('versionsPath')
        version = self.option('version')

        jsonInfoFilePath = os.path.join(versionsPath, version, 'info.json')
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
        if os.path.exists(crawler.var('versionsPath')):
            for node in os.listdir(crawler.var('versionsPath')):
                if os.path.isdir(os.path.join(crawler.var('versionsPath'), node)) and node.startswith('v') and node[1:].isdigit():
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
            elif not os.path.exists(os.path.join(crawler.var('versionsPath'), self.option('version'))):
                raise TaskValidationError(
                    'Version does not exist!'
                )

    def _perform(self):
        """
        Perform the task.
        """
        scriptNode = GafferVersionSwitchTask.currentScriptNode()
        result = []
        for crawler in self.crawlers():
            node = self.fromPathToNode(scriptNode, str(crawler.var('nodePath')))
            selectedVersion = self.option('version')

            # replacing version in the path
            currentFilePath = crawler.var('currentFilePath')
            newFilePath = currentFilePath.replace(
                '/{}/'.format(
                    crawler.var('currentVersion')
                ),
                '/{}/'.format(
                    selectedVersion
                )
            )

            newFilePath = newFilePath.replace(
                '_{}'.format(
                    crawler.var('currentVersion')
                ),
                '_{}'.format(
                    selectedVersion
                )
            )

            try:
                # reference
                if crawler.var('typeName') == 'Reference':
                    node.load(str(newFilePath))
                    continue

                # regular nodes/plugs
                if crawler.var('nestedName'):
                    node = node[str(crawler.var('nestedName'))]

                node[str(crawler.var('plugName'))].setValue(str(newFilePath))
            except Exception:
                sys.stderr.write('Failed on updating {}: {}\n'.format(crawler.var('fullPath'), newFilePath))
                sys.stderr.flush()
                traceback.print_exc()

        return result

    @classmethod
    def toVersionSwitchCrawlers(cls, scriptNode):
        """
        Return a hashmap crawler for the version switch nodes.
        """
        import Gaffer

        result = []
        nodesNeedingUpdate = []
        for childNode in scriptNode.children(Gaffer.Node):
            for nodeInfo in cls.allFilePathNodes(childNode):
                for plugInfo in nodeInfo['plugs']:
                    currentFilePath = plugInfo['fileName']
                    currentVersionPath = cls.versionPath(currentFilePath)

                    if not currentVersionPath:
                        continue

                    currentVersion = os.path.basename(currentVersionPath)
                    versionsPath = os.path.dirname(currentVersionPath)
                    latestVersion = Template(
                        "(latestver '{}' v{})".format(
                            versionsPath,
                            '#' * len(currentVersion[1:])
                        )
                    ).value()

                    nodesNeedingUpdate.append(
                        {
                            'name': nodeInfo['path'],
                            'nodePath': nodeInfo['path'],
                            'typeName': nodeInfo['typeName'].split('::')[-1],
                            'versionsPath': versionsPath,
                            'currentVersion': currentVersion,
                            'currentFilePath': currentFilePath,
                            'latestVersion': latestVersion,
                            'nestedName': plugInfo['nestedName'],
                            'plugName': plugInfo['name'],
                            'fullPath': os.path.join(nodeInfo['path'], plugInfo['name'])
                        }
                    )

        result = []
        for nodeNeedingUpdate in nodesNeedingUpdate:
            hashmapCrawler = Crawler.create(
                {
                    'name': nodeNeedingUpdate['name']
                }
            )
            hashmapCrawler.setVar('dataLayout', 'gafferVersionSwitch')
            hashmapCrawler.setVar('baseName', nodeNeedingUpdate['name'][1:])

            for key, value in nodeNeedingUpdate.items():
                hashmapCrawler.setVar(key, value)

            result.append(hashmapCrawler)

        return result

    @classmethod
    def versionPath(cls, fullPath):
        """
        Return the version path under the full path or empty string.
        """
        versionPartIndex = None
        versionParts = fullPath.split('/')
        for index, filePart in enumerate(reversed(versionParts)):
            if filePart.startswith('v') and filePart[1:].isdigit() and len(filePart[1:]) >= 3:
                versionPartIndex = index
                break

        if versionPartIndex is None:
            return ''

        return '/'.join(versionParts[:-versionPartIndex])

    @classmethod
    def fromPathToNode(cls, scriptNode, path):
        """
        Return the node based on the input path (levels separated by /).
        """
        result = scriptNode
        for level in path.split('/'):
            if not level:
                continue
            result = result[level]

        return result

    @classmethod
    def allFilePathNodes(cls, node, currentPath=''):
        """
        Return a list of dictionaries containing the path for the node and a list of plugs with a file path.
        """
        import Gaffer

        result = []
        currentPlugs = []
        currentPath += "/{}".format(node.getName())
        for plug in node.values():
            nestedName = plug.getName() == 'parameters'

            for childPlug in plug.values() if nestedName else [plug]:
                if not isinstance(childPlug, Gaffer.StringPlug) or childPlug.getInput() or \
                        Gaffer.Metadata.value(childPlug, 'plugValueWidget:type') not in cls.__filePathWidgetTypes:
                    continue

                currentPlugs.append(
                    {
                        'name': childPlug.getName(),
                        'fileName': childPlug.getValue(),
                        'nestedName': plug.getName() if nestedName else None
                    }
                )

        if currentPlugs:
            result.append(
                {
                    'path': currentPath,
                    'typeName': node.typeName(),
                    'plugs': currentPlugs
                }
            )

        if isinstance(node, Gaffer.Box):
            for childNode in node.children(Gaffer.Node):
                result.extend(cls.allFilePathNodes(childNode, currentPath))

        # the file path for the reference is not a plug. However, we treat it
        # as such for convenience
        elif isinstance(node, Gaffer.Reference):
            result.append(
                {
                    'path': currentPath,
                    'typeName': node.typeName(),
                    'plugs': [
                        {
                            'name': 'fileName',
                            'fileName': node.fileName(),
                            'nestedName': None
                        }
                    ]
                }
            )

        return result

    @classmethod
    def __camelCaseToSpaced(cls, text):
        """
        Return the input camelCase string to spaced.
        """
        return text[0].upper() + re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>", text[1:])


# registering task
GafferTask.register(
    'gafferVersionSwitch',
    GafferVersionSwitchTask
)

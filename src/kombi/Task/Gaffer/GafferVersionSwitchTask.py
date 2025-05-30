import os
import json
import sys
import time
import traceback
from ..Task import Task, TaskError, TaskValidationError
from ..External.GafferTask import GafferTask
from ...Template import Template
from ...Element import Element

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

    def switchInfo(self, elements):
        """
        Return a text output displayed in the info area of the element.
        """
        versionsPath = elements[0].var('versionsPath')
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
            output.append("{}: {}".format(Template.runProcedure('camelcasetospaced', key), value))

        return '\n'.join(output)

    def setup(self, elements):
        """
        Setting the initial value for output dir.
        """
        element = elements[0]

        versions = set()
        if os.path.exists(element.var('versionsPath')):
            for node in os.listdir(element.var('versionsPath')):
                if os.path.isdir(os.path.join(element.var('versionsPath'), node)) and node.startswith('v') and node[1:].isdigit():
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
            elif not os.path.exists(os.path.join(element.var('versionsPath'), self.option('version'))):
                raise TaskValidationError(
                    'Version does not exist!'
                )

    def _perform(self):
        """
        Perform the task.
        """
        scriptNode = GafferVersionSwitchTask.currentScriptNode()
        result = []
        for element in self.elements():
            node = self.fromPathToNode(scriptNode, str(element.var('nodePath')))
            selectedVersion = self.option('version')

            # replacing version in the path
            currentFilePath = element.var('currentFilePath')
            newFilePath = currentFilePath.replace(
                '/{}/'.format(
                    element.var('currentVersion')
                ),
                '/{}/'.format(
                    selectedVersion
                )
            )

            newFilePath = newFilePath.replace(
                '_{}'.format(
                    element.var('currentVersion')
                ),
                '_{}'.format(
                    selectedVersion
                )
            )

            try:
                # reference
                if element.var('typeName') == 'Reference':
                    node.load(str(newFilePath))
                    continue

                # regular nodes/plugs
                if element.var('nestedName'):
                    node = node[str(element.var('nestedName'))]

                node[str(element.var('plugName'))].setValue(str(newFilePath))
            except Exception:
                sys.stderr.write('Failed on updating {}: {}\n'.format(element.var('fullPath'), newFilePath))
                sys.stderr.flush()
                traceback.print_exc()

        return result

    @classmethod
    def toVersionSwitchElements(cls, scriptNode):
        """
        Return a hashmap element for the version switch nodes.
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
                        "!kt (latestver '{}' v{})".format(
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
            hashmapElement = Element.create(
                {
                    'name': nodeNeedingUpdate['name']
                }
            )
            hashmapElement.setVar('dataLayout', 'gafferVersionSwitch')
            hashmapElement.setVar('baseName', nodeNeedingUpdate['name'][1:])

            for key, value in nodeNeedingUpdate.items():
                hashmapElement.setVar(key, value)

            result.append(hashmapElement)

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


# registering task
GafferTask.register(
    'gafferVersionSwitch',
    GafferVersionSwitchTask
)

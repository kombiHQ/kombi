import os
import glob
from ..Task import Task
from ..Template import Template
from ..TaskHolder import TaskHolder
from ..Resource import Resource
from .TaskHolderLoader import TaskHolderLoader, TaskHolderLoaderError

class PythonLoaderContentError(TaskHolderLoaderError):
    """Python Loader Content Error."""

class PythonLoader(TaskHolderLoader):
    """
    Loads configuration from json files.
    """

    def load(self, contents, contextVars={}):
        """
        Load taskHolders from a python data structure to a task holder.

        Expected format:
        {
          "scripts": [
            "*/*.py"
          ],
          "vars": {
            "prefix": "/tmp/test",
            "__uiHintSourceColumns": [
                "shot",
                "type"
            ]
          },
          "tasks": [
            {
              "run": "convertImage",
              "target": "{prefix}/foo/sequences/{seq}/{shot}/online/publish/elements/{plateName}/(newver <parent>).(pad {frame} 4).exr",
              "filter": "",
              "status": "execute",
              "export": "{prefix}/result/{sessionId}/resultCrawlersFromConvertImage.json"
              "metadata": {
                "match.types": [
                    "dpxPlate"
                ],
                "match.vars": {
                    "imageType": [
                        "sequence"
                    ]
                },
                "dispatch.await": True
              },
              "tasks": [
                {
                  "run": "movGen",
                  "target": "{prefix}/foo/sequences/{seq}/{shot}/online/review/{name}.mov",
                  "metadata": {
                    "match.types": [
                        "exrPlate"
                    ],
                    "match.vars": {
                        "imageType": [
                            "sequence"
                        ]
                    }
                  }
                },
                {
                    "include": "../../myTaskHolderInfo.json"
                }
              ]
            }
          ]
        }
        """
        # root checking
        if not isinstance(contents, dict):
            raise PythonLoaderContentError('Expecting object as root!')

        # loading scripts
        # TODO: move this part to the task holder loader
        if 'scripts' in contents:

            # scripts checking
            if not isinstance(contents['scripts'], list):
                raise PythonLoaderContentError('Expecting a list of scripts!')

            for script in contents['scripts']:
                if not os.path.isabs(script):
                    if not contextVars.get('configDirectory', ''):
                        raise PythonLoaderContentError(
                            "configDirectory is empty! Can't resolve scripts with relative path: {}".format(
                                script
                            )
                        )
                    script = os.path.join(contextVars['configDirectory'], script)
                scriptFiles = glob.glob(script)

                # loading resource
                for scriptFile in scriptFiles:
                    Resource.get().load(scriptFile)

        # parsing root context vars
        self.__loadTaskHolder(contents, contextVars)

    def __loadTaskHolder(self, contents, contextVars, parentTaskHolder=None):
        """
        Load a task holder contents.
        """
        # loading task holders
        if 'tasks' not in contents:
            return

        contextVars = dict(list(contextVars.items()) + list(self.__parseVars(contents).items()))

        # task holders checking
        if not isinstance(contents['tasks'], list):
            raise PythonLoaderContentError('Expecting a list of task holders!')

        for taskHolderInfo in contents['tasks']:

            # task holder info checking
            if not isinstance(taskHolderInfo, dict):
                raise PythonLoaderContentError('Expecting an object to describe the task holder!')

            taskHolderInfo = self.__expandTaskHolderInfo(taskHolderInfo, contextVars)

            task = self.__parseTask(taskHolderInfo)

            # getting the target template
            targetTemplate = Template(taskHolderInfo.get('target', ''))

            # getting the filter template
            filterTemplate = Template(taskHolderInfo.get('filter', ''))

            # getting the export template
            exportTemplate = Template(taskHolderInfo.get('export', ''))

            # creating a task holder
            taskHolder = TaskHolder(
                task,
                targetTemplate,
                filterTemplate,
                exportTemplate
            )

            # loading imports
            self.__loadImports(taskHolder, taskHolderInfo)

            # setting status of the task holder
            if 'status' in taskHolderInfo:
                taskHolder.setStatus(taskHolderInfo['status'])

            # adding variables to the task holder
            for varName, varValue in list(contextVars.items()) + list(self.__parseVars(taskHolderInfo).items()):
                taskHolder.addVar(
                    varName,
                    varValue,
                    isContextVar=True
                )

            if parentTaskHolder:
                parentTaskHolder.addSubTaskHolder(
                    taskHolder
                )
            else:
                self.addTaskHolder(taskHolder)

            # loading sub task holders recursively
            if 'tasks' in contents:
                self.__loadTaskHolder(
                    taskHolderInfo,
                    contextVars,
                    parentTaskHolder=taskHolder
                )

    @classmethod
    def __loadImports(cls, taskHolder, taskHolderInfo):
        """
        Load imports to the task holder.
        """
        if 'import' not in taskHolderInfo:
            return

        importTemplates = taskHolderInfo['import']

        if not isinstance(importTemplates, (tuple, list)):
            importTemplates = (importTemplates)

        for importTemplate in importTemplates:
            taskHolder.addImportTemplate(
                Template(importTemplate)
            )

    @classmethod
    def __expandTaskHolderInfo(cls, taskHolderInfo, contextVars):
        """
        Return the expanded content of a task holder that can be described using an external resource.
        """
        # special case where configurations can be defined externally, when that
        # is the case loading that instead
        if 'include' not in taskHolderInfo:
            return taskHolderInfo

        # detecting if the path is absolute or needs to be resolved
        if os.path.isabs(taskHolderInfo['include']):
            includePath = taskHolderInfo['include']
        else:
            if not contextVars.get('configDirectory', ''):
                raise PythonLoaderContentError(("configDirectory is empty! Can't resolve include with relative path: {}").format(taskHolderInfo['include']))
            includePath = os.path.normpath(os.path.join(contextVars['configDirectory'], taskHolderInfo['include']))

        del taskHolderInfo['include']

        # looking for a loader of the include
        ext = os.path.splitext(includePath)[-1][1:]
        loaded = False
        if ext in cls.registeredNames():
            taskHolderLoader = cls.create(ext)
            if isinstance(taskHolderLoader, PythonLoader):

                # loading include
                with open(includePath) as f:

                    # parsing include
                    includeTaskHolderInfo = taskHolderLoader.parse(f.read())

                    # making sure the parsed data contains the right structure
                    if not isinstance(includeTaskHolderInfo, dict):
                        raise PythonLoaderContentError('Expecting an object to describe the task holder!')

                    # in case any information has been overridden in the include declaration
                    # we want to preserve it and combine with all the other information
                    # coming from the task holder
                    for key in filter(lambda x: x not in taskHolderInfo, includeTaskHolderInfo.keys()):
                        taskHolderInfo[key] = includeTaskHolderInfo[key]

                    # adding config information
                    if 'vars' not in taskHolderInfo:
                        taskHolderInfo['vars'] = {}
                    taskHolderInfo['vars'] = dict(list(contextVars.items()) + list(taskHolderInfo['vars'].items()))
                    taskHolderInfo['vars']['configDirectory'] = os.path.dirname(includePath)
                    taskHolderInfo['vars']['contextConfig'] = includePath
                    loaded = True

        if not loaded:
            raise PythonLoaderContentError(
                'Could not find loader for include: {}'.format(includePath)
            )

        return taskHolderInfo

    @classmethod
    def __parseTask(cls, taskHolderInfo):
        """
        Return a task object parsed under the taskHolderInfo.
        """
        task = Task.create(taskHolderInfo['run'])

        # setting task options
        if 'options' in taskHolderInfo:
            for taskOptionName, taskOptionValue in taskHolderInfo['options'].items():
                task.setOption(taskOptionName, taskOptionValue)

        # setting task metadata
        if 'metadata' in taskHolderInfo:
            for taskMetadataName, taskMetadataValue in taskHolderInfo['metadata'].items():
                task.setMetadata(taskMetadataName, taskMetadataValue)

        return task

    @classmethod
    def __parseVars(cls, contents):
        """
        Return the variables defined inside of the contents.
        """
        result = {}
        if 'vars' in contents:
            # vars checking
            if not isinstance(contents['vars'], dict):
                raise PythonLoaderContentError('Expecting a list of vars!')
            result = dict(contents['vars'])

        return result

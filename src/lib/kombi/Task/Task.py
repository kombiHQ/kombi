import json
from collections import OrderedDict
from ..Resource import Resource
from ..InfoCrate.Fs import FsInfoCrate
from ..InfoCrate import InfoCrate
from ..Template import Template
from ..TaskReporter import TaskReporter

class TaskError(Exception):
    """Task error."""

class TaskTypeNotFoundError(TaskError):
    """Task type not found error."""

class TaskValidationError(TaskError):
    """Task validation error."""

class TaskInvalidInfoCrateError(TaskError):
    """Task Invalid infoCrate error."""

class TaskInvalidOptionError(TaskError):
    """Task invalid option error."""

class TaskInvalidMetadataError(TaskError):
    """Task invalid metadata error."""

class Task(object):
    """
    Abstract Task.

    A task is used to operate over file paths resolved by the template runner.

    Task Metadata:
        - output.reporter: name of the reporter used to display the output of the task or none (empty string)
    """

    __registered = {}

    def __init__(self, taskType):
        """
        Create a task object.
        """
        self.__infoCrates = OrderedDict()
        self.__metadata = {}
        self.__taskType = taskType
        self.__options = OrderedDict()

    def type(self):
        """
        Return the task type.
        """
        return self.__taskType

    def metadata(self, scope=''):
        """
        Return the metadata.

        The metadata is represented as dictionary. You can query the entire
        metadata by passing an empty string as scope (default). Otherwise,
        you can pass a scope string separating each level by '.' (for instance:
        first.second.third).
        """
        if not scope:
            return self.__metadata

        currentLevel = self.__metadata
        for level in scope.split('.'):
            if level not in currentLevel:
                raise TaskInvalidMetadataError(
                    'Invalid metadata "{}"'.format(scope)
                )

            currentLevel = currentLevel[level]

        return currentLevel

    def setMetadata(self, scope, value):
        """
        Set an arbitrary metadata.

        In case you want to set a multi-dimension value under the metadata,
        you can you the scope for it by passing the levels separated by "."
        (The levels are created automatically as new dictionaries in case they
        don't exist yet). Make sure the data being set inside of the metadata
        can be serialized through json.
        """
        assert scope, "scope cannot be empty"

        # we want to store an immutable value under the metadata
        safeValue = json.loads(json.dumps(value))

        # creating auxiliary levels
        levels = scope.split('.')
        currentLevel = self.__metadata
        for level in levels[:-1]:
            if level not in currentLevel:
                currentLevel[level] = {}

            currentLevel = currentLevel[level]

        currentLevel[levels[-1]] = safeValue

    def metadataNames(self):
        """
        Return a list with the names of the root levels under the metadata.
        """
        return list(self.__metadata.keys())

    def hasMetadata(self, scope):
        """
        Return a boolean telling if the input scope is under the metadata.

        In case the scope is empty, then the result is done based if there's
        any information under the metadata.
        """
        if not scope:
            return bool(len(self.__metadata))

        levels = scope.split('.')
        currentLevel = self.__metadata
        found = True
        for level in levels[:-1]:
            if not isinstance(currentLevel, dict) or level not in currentLevel:
                found = False
                break
            currentLevel = currentLevel[level]

        if found and levels[-1] in currentLevel:
            return True

        return False

    def option(self, name):
        """
        Return a value for an option.
        """
        if name not in self.__options:
            raise TaskInvalidOptionError(
                'Invalid option name: "{0}"'.format(
                    name
                )
            )

        return self.__options[name]

    def templateOption(self, name, infoCrate=None, extraVars={}):
        """
        Return the resolved value of an option.
        """
        optionValue = self.option(name)

        # 2d hashmap
        if isinstance(optionValue, dict):
            result = {}
            for key, value in optionValue.items():
                result[key] = self.__resolveTemplateValue(value, infoCrate, extraVars)
            return result

        # 2d array
        elif isinstance(optionValue, (list, tuple)):
            result = []
            for value in optionValue:
                result.append(self.__resolveTemplateValue(value, infoCrate, extraVars))
            return result

        return self.__resolveTemplateValue(optionValue, infoCrate, extraVars)

    def setOption(self, name, value):
        """
        Set an option to the task.
        """
        self.__options[name] = value

    def setOptions(self, **kwargs):
        """
        Helper to set multiple options at once to the task.

        The options are expected to te passed as keyword parameters.
        """
        for optionName, optionValue in kwargs.items():
            self.setOption(optionName, optionValue)

    def optionNames(self):
        """
        Return a list of the option names.
        """
        return list(self.__options.keys())

    def target(self, infoCrate):
        """
        Return the target file path for infoCrate.
        """
        if infoCrate not in self.__infoCrates:
            raise TaskInvalidInfoCrateError(
                'InfoCrate is not part of the task!'
            )

        return self.__infoCrates[infoCrate]

    def infoCrates(self):
        """
        Return a list of infoCrates associated with the task.
        """
        return list(self.__infoCrates.keys())

    def add(self, infoCrate, targetFilePath=''):
        """
        Add a infoCrate to the task.

        A target file path can be associated with the infoCrate. It should be
        used by tasks that generate files. This information may be provided
        by tasks executed through a task holder where the template in the
        task holder is resolved and passed as target when adding
        the infoCrate to the task.
        """
        assert isinstance(infoCrate, InfoCrate), \
            "Invalid InfoCrate!"

        assert isinstance(targetFilePath, str), \
            "targetFilePath needs to be defined as string"

        self.__infoCrates[infoCrate] = targetFilePath

    def clear(self):
        """
        Remove all infoCrates associated with the task.
        """
        self.__infoCrates.clear()

    def output(self, taskReporter=None):
        """
        Perform and result a list of infoCrates created by task.
        """
        reporterName = self.hasMetadata('output.reporter') and self.metadata('output.reporter')
        reporter = None
        if reporterName:
            reporter = TaskReporter.create(reporterName, self.type())

        contextVars = {}
        for infoCrate in self.infoCrates():
            for ctxVarName in infoCrate.contextVarNames():
                if ctxVarName not in contextVars:
                    contextVars[ctxVarName] = infoCrate.var(ctxVarName)

        # validating input
        self.validate(self.infoCrates())

        # performing task
        outputInfoCrates = self._perform()

        # Copy all context variables to output infoCrates
        for outputInfoCrate in outputInfoCrates:
            if reporter:
                reporter.addInfoCrate(outputInfoCrate)

            for ctxVarName in filter(lambda x: x not in outputInfoCrate.varNames(), contextVars):
                outputInfoCrate.setVar(
                    ctxVarName,
                    contextVars[ctxVarName],
                    True
                )

        if reporter:
            reporter.display()

        return outputInfoCrates

    def clone(self):
        """
        Clone the current task.
        """
        clone = self.__class__(self.type())

        # copying options
        for optionName in self.optionNames():
            clone.setOption(optionName, self.option(optionName))

        # copying metadata
        for metadataName in self.metadataNames():
            clone.setMetadata(metadataName, self.metadata(metadataName))

        # copying infoCrates
        for infoCrate in self.infoCrates():
            clone.add(infoCrate, self.target(infoCrate))

        return clone

    def toJson(self):
        """
        Serialize a task to json (it can be loaded later through createFromJson).
        """
        contents = {
            "type": self.type()
        }

        # current metadata
        metadata = self.metadata()

        # current options
        options = {}
        for optionName in self.optionNames():
            options[optionName] = self.option(optionName)

        # infoCrate data
        infoCrateData = []
        for infoCrate in self.infoCrates():
            infoCrateData.append({
                'filePath': self.target(infoCrate),
                'serializedInfoCrate': infoCrate.toJson()
            })

        # custom resources
        loadedResources = Resource.get().loaded(ignoreFromEnvironment=True)

        # only including them as result if they are not empty
        if len(metadata):
            contents['metadata'] = metadata

        if len(options):
            contents['options'] = options

        if len(infoCrateData):
            contents['infoCrateData'] = infoCrateData

        if len(loadedResources):
            contents['resources'] = loadedResources

        return json.dumps(
            contents,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        )

    @staticmethod
    def register(name, taskClass):
        """
        Register a task type.
        """
        assert issubclass(taskClass, Task), \
            "Invalid task class!"

        Task.__registered[name] = taskClass

    @staticmethod
    def registeredNames():
        """
        Return a list of registered tasks.
        """
        return list(Task.__registered.keys())

    @staticmethod
    def create(taskType, *args, **kwargs):
        """
        Create a task object.
        """
        if taskType not in Task.__registered:
            raise TaskTypeNotFoundError(
                'Task name is not registered: "{0}"'.format(
                    taskType
                )
            )
        return Task.__registered[taskType](taskType, *args, **kwargs)

    @staticmethod
    def createFromJson(jsonContents):
        """
        Create a task based on the jsonContents (serialized via toJson).
        """
        contents = json.loads(jsonContents)
        taskType = contents["type"]
        taskOptions = contents.get("options", {})
        taskMetadata = contents.get("metadata", {})
        infoCrateData = contents.get("infoCrateData", [])
        loadResources = contents.get("resources", [])

        # loading resources
        for loadResource in loadResources:
            if loadResource in Resource.get().loaded():
                continue
            Resource.get().load(loadResource)

        # loading task
        task = Task.create(taskType)

        # setting task options
        for optionName, optionValue in taskOptions.items():
            task.setOption(optionName, optionValue)

        # setting task metadata
        for metadataName, metadataValue in taskMetadata.items():
            task.setMetadata(metadataName, metadataValue)

        # adding infoCrates
        for infoCrateDataItem in infoCrateData:
            filePath = infoCrateDataItem['filePath']
            infoCrate = InfoCrate.createFromJson(
                infoCrateDataItem['serializedInfoCrate']
            )
            task.add(infoCrate, filePath)

        return task

    def _perform(self):
        """
        For re-implementation: should implement the computation of the task and return a list of infoCrates as output.

        The default implementation return a list of infoCrates based on the target filePath (The filePath is provided by
        by the template). In case none file path has not been specified then returns an empty list of infoCrates.
        """
        filePaths = []
        for infoCrate in self.infoCrates():
            filePath = self.target(infoCrate)
            if filePath and filePath not in filePaths:
                filePaths.append(filePath)

        return list(map(FsInfoCrate.createFromPath, filePaths))

    def validate(self, infoCrates=None):
        """
        For re-implementation: should implement a check for the task.

        This method is called right before performing the task. Also, it can be called by
        user interfaces for validating user input (options).

        In order to report a validation failure make sure to raise the exception TaskValidationError
        with the message about the failure. Otherwise, in case of no failure then no result is needed.
        """

    def __resolveTemplateValue(self, value, infoCrate, extraVars):
        """
        Resolve the template value.
        """
        if not isinstance(value, str):
            return value
        elif infoCrate is not None:
            return Template(value).valueFromInfoCrate(infoCrate, extraVars)

        return Template(value).value(extraVars)

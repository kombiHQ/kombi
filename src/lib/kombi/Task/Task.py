import os
import json
import sys
import copy
from typing import List
from collections import OrderedDict
from ..ResourceLoader import ResourceLoader
from ..Element.Fs import FsElement
from ..Element import Element
from ..Template import Template
from ..TaskReporter import TaskReporter
from ..KombiError import KombiError

# optional dependency
try:
    import pycallgraph
except ImportError:
    hasPyCallGraph = False
else:
    hasPyCallGraph = True

class TaskError(KombiError):
    """Task error."""

class TaskTypeNotFoundError(TaskError):
    """Task type not found error."""

class TaskValidationError(TaskError):
    """Task validation error."""

class TaskInvalidElementError(TaskError):
    """Task Invalid element error."""

class TaskInvalidOptionError(TaskError):
    """Task invalid option error."""

class TaskInvalidMetadataError(TaskError):
    """Task invalid metadata error."""

class _TaskSentinelValue:
    """Task sentinel value."""

class Task(object):
    """
    Abstract Task.

    A task is used to operate over file paths resolved by the template runner.

    Task Metadata:
        - output.reporter: name of the reporter used to display the output of the task or none (empty string)
        - output.profile: file path used to profile the execution and exporting it as a PNG heatmap
    """

    __registered = {}
    __sentinelValue = _TaskSentinelValue()
    __dotExecutable = os.environ.get(
        'KOMBI_GRAPHVIZ_DOT_EXECUTABLE',
        'dot'
    )

    def __init__(self, taskType):
        """
        Create a task object.
        """
        self.__elements = OrderedDict()
        self.__metadata = {}
        self.__taskType = taskType
        self.__options = OrderedDict()
        self.__currentElement = None

    def type(self) -> str:
        """
        Return the task type.
        """
        return self.__taskType

    def metadata(self, scope='', defaultValue=__sentinelValue):
        """
        Return the metadata.

        The metadata is represented as dictionary. You can query the entire
        metadata by passing an empty string as scope (default). Otherwise,
        you can pass a scope string separating each level by '.' (for instance:
        first.second.third).

        In case a defaultValue is not specified this method will raise the
        exception TaskInvalidMetadataError when the metadata does not exist.
        """
        if not scope:
            return self.__metadata

        currentLevel = self.__metadata
        for level in scope.split('.'):
            if level not in currentLevel:

                if defaultValue is self.__sentinelValue:
                    raise TaskInvalidMetadataError(
                        'Invalid metadata "{}"'.format(scope)
                    )
                else:
                    return defaultValue

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

    def metadataNames(self) -> List[str]:
        """
        Return a list with the names of the root levels under the metadata.
        """
        return list(self.__metadata.keys())

    def hasMetadata(self, scope) -> bool:
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

    def option(self, name, element=None, extraVars={}):
        """
        Return a value for an option.
        """
        if name not in self.__options:
            raise TaskInvalidOptionError(
                'Invalid option name: "{0}"'.format(
                    name
                )
            )

        # Check if a template is defined for the given option:
        # 1. First, perform a strict metadata lookup
        # 2. If no metadata is found, check if the option value represents a template
        templateMetadata = f'task.options.{name}.template'
        if self.metadata(templateMetadata, False) or \
                not self.hasMetadata(templateMetadata) and Template.hasTemplatePrefix(self.__options[name]):
            # when element is not provided, determine the default element
            if element is None:
                if self.__currentElement:
                    element = self.__currentElement
                elif self.elements():
                    element = self.elements()[0]

            if element:
                return self.__templateOption(name, element, extraVars)

        return self.__options[name]

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

    def optionNames(self) -> List[str]:
        """
        Return a list of the option names.
        """
        return list(self.__options.keys())

    def target(self, element) -> str:
        """
        Return the target file path for element.
        """
        if element not in self.__elements:
            raise TaskInvalidElementError(
                'Element is not part of the task!'
            )

        return self.__elements[element]

    def elements(self) -> List[Element]:
        """
        Return a list of elements associated with the task.
        """
        return list(self.__elements.keys())

    def add(self, element, targetFilePath=''):
        """
        Add a element to the task.

        A target file path can be associated with the element. It should be
        used by tasks that generate files. This information may be provided
        by tasks executed through a task holder where the template in the
        task holder is resolved and passed as target when adding
        the element to the task.
        """
        assert isinstance(element, Element), \
            "Invalid Element!"

        assert isinstance(targetFilePath, str), \
            "targetFilePath needs to be defined as string"

        self.__elements[element] = targetFilePath

    def clear(self):
        """
        Remove all elements associated with the task.
        """
        self.__elements.clear()

    def setup(self, elements):
        """
        Prepares the task before it is presented in the UI.

        This method is called by the UI prior to presenting the task. The provided
        'elements' are the ones used to execute the task. It can be utilized to
        initialize metadata, set default values, or configure options specific to
        the task.
        """

    def output(self) -> List[Element]:
        """
        Perform and result a list of elements created by task.
        """
        reporterName = self.hasMetadata('output.reporter') and self.metadata('output.reporter')
        reporter = None
        if reporterName:
            reporter = TaskReporter.create(reporterName, self.type())

        contextVars = {}
        for element in self.elements():
            for ctxVarName in element.contextVarNames():
                if ctxVarName not in contextVars:
                    contextVars[ctxVarName] = element.var(ctxVarName)

        # validating input
        self.validate(self.elements())

        # performing task
        outputElements = []

        profiledExecution = False
        if self.hasMetadata('output.profile') and self.metadata('output.profile'):
            if not hasPyCallGraph:
                sys.stderr.write(
                    'Error, unable to profile execution. The "pycallgraph" dependency is missing!\n'
                )
                sys.stderr.flush()
            else:
                profiledExecution = True
                graphviz = pycallgraph.output.GraphvizOutput()
                graphviz.output_file = self.metadata('output.profile')
                graphviz.tool = self.__dotExecutable
                with pycallgraph.PyCallGraph(output=graphviz):
                    outputElements.extend(self._perform())

                sys.stdout.write(
                    'Execution profile has been saved to: {}\n'.format(graphviz.output_file)
                )
                sys.stdout.flush()

        if not profiledExecution:
            outputElements.extend(self._perform())

        # Copy all context variables to output elements
        for outputElement in outputElements:
            if reporter:
                reporter.addElement(outputElement)

            for ctxVarName in filter(lambda x: x not in outputElement.varNames(), contextVars):
                outputElement.setVar(
                    ctxVarName,
                    contextVars[ctxVarName],
                    True
                )

        if reporter:
            reporter.display()

        return outputElements

    def clone(self) -> 'Task':
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

        # copying elements
        for element in self.elements():
            clone.add(element, self.target(element))

        return clone

    def validate(self, elements=None):
        """
        For re-implementation: should implement a check for the task.

        This method is called right before performing the task. Also, it can be called by
        user interfaces for validating user input (options).

        In order to report a validation failure make sure to raise the exception TaskValidationError
        with the message about the failure. Otherwise, in case of no failure then no result is needed.
        """

    def toJson(self) -> str:
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
        elementOptions = {}
        for optionName in self.optionNames():
            optionValue = self.option(optionName)

            # handling when elements are used as option value
            if optionValue is not None and isinstance(optionValue, Element):
                optionValue = optionValue.toJson()
                elementOptions[optionName] = None

            # complex deep structures
            elif optionValue is not None and isinstance(optionValue, (tuple, list, dict)):
                currentPath = []
                optionElements = self.__optionElementLevels(optionValue, currentPath)
                if optionElements:
                    elementOptions[optionName] = optionElements
                    optionValue = copy.deepcopy(optionValue)
                    for optionElementLevels in optionElements:
                        currentLevel = optionValue
                        for optionElementLevel in optionElementLevels:
                            if isinstance(currentLevel[optionElementLevel], Element):
                                currentLevel[optionElementLevel] = currentLevel[optionElementLevel].toJson()
                            else:
                                currentLevel = currentLevel[optionElementLevel]

            options[optionName] = optionValue

        # element data
        elementData = []
        for element in self.elements():
            elementData.append({
                'filePath': self.target(element),
                'serializedElement': element.toJson()
            })

        # custom resources
        loadedResources = ResourceLoader.get().loaded(ignoreFromEnvironment=True)

        # only including them as result if they are not empty
        if len(metadata):
            contents['metadata'] = metadata

        if len(options):
            contents['options'] = options
            contents['elementOptions'] = elementOptions

        if len(elementData):
            contents['elementData'] = elementData

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
    def registeredNames() -> List[str]:
        """
        Return a list of registered tasks.
        """
        return list(Task.__registered.keys())

    @staticmethod
    def create(taskType, *args, **kwargs) -> 'Task':
        """
        Create a task object.
        """
        if taskType not in Task.__registered:
            raise TaskTypeNotFoundError(
                'Task name is not registered: "{0}"'.format(
                    taskType
                )
            )
        task = Task.__registered[taskType](taskType, *args, **kwargs)
        if not task.hasMetadata('name'):
            task.setMetadata('name', taskType)
        return task

    @staticmethod
    def createFromJson(jsonContents) -> 'Task':
        """
        Create a task based on the jsonContents (serialized via toJson).
        """
        contents = json.loads(jsonContents)
        taskType = contents["type"]
        taskOptions = contents.get("options", {})
        elementOptions = contents.get("elementOptions", {})
        taskMetadata = contents.get("metadata", {})
        elementData = contents.get("elementData", [])
        loadResources = contents.get("resources", [])

        # loading resources
        for loadResource in loadResources:
            if loadResource in ResourceLoader.get().loaded():
                continue
            ResourceLoader.get().load(loadResource)

        # loading task
        task = Task.create(taskType)

        # setting task options
        for optionName, optionValue in taskOptions.items():
            # restoring elements
            if optionName in elementOptions:
                if elementOptions[optionName] is None:
                    optionValue = Element.createFromJson(optionValue)
                else:
                    optionValue = copy.deepcopy(optionValue)
                    optionElements = elementOptions[optionName]
                    for optionElementLevels in optionElements:
                        currentLevel = optionValue
                        for index, optionElementLevel in enumerate(optionElementLevels):
                            if index == len(optionElementLevels) - 1:
                                currentLevel[optionElementLevel] = Element.createFromJson(currentLevel[optionElementLevel])
                            else:
                                currentLevel = currentLevel[optionElementLevel]

            task.setOption(optionName, optionValue)

        # setting task metadata
        for metadataName, metadataValue in taskMetadata.items():
            task.setMetadata(metadataName, metadataValue)

        # adding elements
        for elementDataItem in elementData:
            filePath = elementDataItem['filePath']
            element = Element.createFromJson(
                elementDataItem['serializedElement']
            )
            task.add(element, filePath)

        return task

    def _processElement(self, element) -> Element | None:
        """
        Process an individual element.

        This method is a placeholder and should be re-implemented by derived classes to define how each
        element is processed.
        By default, it checks if the element has a valid target file path and creates a corresponding
        file system element. If the file path is not defined, it returns None instead.

        Derived classes can override this method to implement custom processing logic.
        """
        targetPath = self.target(element)
        if targetPath:
            return FsElement.createFromPath(targetPath)
        return None

    def _perform(self) -> List[Element]:
        """
        To be overridden: This method should implement the task computation and return a list of processed elements.

        The default implementation iterates over a list of elements, processing each element using the _processElement method.
        By default, _processElement checks if the element has an associated target file path (provided by the template) and
        returns the corresponding file system element if available.

        Derived classes should override _processElement to provide specific processing logic tailored to their needs.
        """
        result = []
        alreadyAdded = set()

        for element in self.elements():
            self.__currentElement = element
            targetPath = self.target(element)
            resultElement = self._processElement(element)
            # in case the target path is defined and it's the same, don't include the element
            # again to the result...
            if resultElement and targetPath not in alreadyAdded:
                result.append(resultElement)
                if targetPath:
                    alreadyAdded.add(targetPath)

        return result

    def __optionElementLevels(self, data, currentPath):
        """
        Utility method recursively traverses through all levels of nested structures to find elements.
        """
        result = []
        if data is None:
            return result

        if isinstance(data, (list, tuple)):
            for index, item in enumerate(data):
                result += self.__optionElementLevels(item, currentPath + [index])
        elif isinstance(data, dict):
            for key, value in data.items():
                result += self.__optionElementLevels(value, currentPath + [key])
        elif isinstance(data, Element):
            result.append(currentPath)

        return result

    def __templateOption(self, name, element=None, extraVars={}):
        """
        Return the resolved value of an option.
        """
        optionValue = self.__options[name]

        # 2d hashmap
        if isinstance(optionValue, dict):
            result = {}
            for key, value in optionValue.items():
                result[key] = self.__resolveTemplateValue(value, element, extraVars)
            return result

        # 2d array
        elif isinstance(optionValue, (list, tuple)):
            result = []
            for value in optionValue:
                result.append(self.__resolveTemplateValue(value, element, extraVars))
            return result

        return self.__resolveTemplateValue(optionValue, element, extraVars)

    def __resolveTemplateValue(self, value, element, extraVars):
        """
        Resolve the template value.
        """
        if not isinstance(value, str):
            return value
        elif element is not None:
            return Template(value).valueFromElement(element, extraVars)

        return Template(value).value(extraVars)

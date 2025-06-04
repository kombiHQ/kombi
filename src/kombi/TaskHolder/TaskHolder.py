import os
import json
import pathlib
from collections import OrderedDict
from fnmatch import fnmatch
from ..Task import Task
from ..TaskWrapper import TaskWrapper
from ..Template import Template
from ..Element import Element, Matcher
from ..KombiError import KombiError

class TaskHolderError(KombiError):
    """Task holder error."""

class TaskHolderInvalidVarNameError(TaskHolderError):
    """Task holder invalid var name error."""

class TaskHolderInvalidTagNameError(TaskHolderError):
    """Task holder invalid tag name error."""

class _TaskHolderSentinelValue:
    """Task holder sentinel value."""

class TaskHolder(object):
    """
    Holds task and sub task holders associated with a target template and element matcher.

    Task Metadata:
        - wrapper.name: string with the name of the task wrapper used to execute the task
        - wrapper.options: dict containing the options passed to the task wrapper
        - match.types: list containing the types used to match the elements
        - match.vars: dict containing the key and value for the variables used to match the elements
    """

    statusTypes = (
        'execute',
        'bypass',
        'ignore'
    )
    __sentinelValue = _TaskHolderSentinelValue()

    def __init__(self, task, targetTemplate=None, filterTemplate=None, exportTemplate=None, profileTemplate=None):
        """
        Create a task holder object.
        """
        self.setTask(task)

        self.__subTaskHolders = []
        self.__contextVarNames = set()
        self.__importTemplates = []
        self.__regroupTagName = ''
        self.setStatus(self.statusTypes[0])

        # setting target template
        if targetTemplate is None:
            targetTemplate = Template()
        self.__setTargetTemplate(targetTemplate)

        # setting filter template
        if filterTemplate is None:
            filterTemplate = Template()
        self.__setFilterTemplate(filterTemplate)

        # setting export template
        if exportTemplate is None:
            exportTemplate = Template()
        self.__setExportTemplate(exportTemplate)

        # setting profile template
        if profileTemplate is None:
            profileTemplate = Template()
        self.__setProfileTemplate(profileTemplate)

        # creating element matcher
        matchTypes = []
        if task.hasMetadata('match.types'):
            matchTypes = task.metadata('match.types')

        matchVars = {}
        if task.hasMetadata('match.vars'):
            matchVars = task.metadata('match.vars')

        matcher = Matcher(matchTypes, matchVars)
        self.__setMatcher(matcher)

        # creating task wrapper
        taskWrapperName = "default"
        taskWrapperOptions = {}
        if task.hasMetadata('wrapper.name'):
            taskWrapperName = task.metadata('wrapper.name')

            if task.hasMetadata('wrapper.options'):
                taskWrapperOptions = task.metadata('wrapper.options')

        taskWrapper = TaskWrapper.create(taskWrapperName)
        for optionName, optionValue in taskWrapperOptions.items():
            taskWrapper.setOption(
                optionName,
                optionValue
            )
        self.__setTaskWrapper(taskWrapper)
        self.__vars = {}
        self.__tags = {}

    def setRegroupTag(self, groupTagName):
        """
        Set the name of the tag used to re-group the input elements.

        It works by splitting the task execution for each group (empty
        string means no regroup is being associated).
        """
        self.__regroupTagName = groupTagName

    def regroupTag(self):
        """
        Return the re-group tag name.
        """
        return self.__regroupTagName

    def setStatus(self, status):
        """
        Set a status for the task holder used when running the task.

        Status:
            - execute: perform the task normally (default)
            - bypass: bypass the execution of the task and passes the source
            elements as result for subtasks
            - ignore: ignore the execution of the task and subtasks
        """
        assert status in self.statusTypes, \
            "Invalid status {}!".format(status)

        self.__status = status

    def status(self):
        """
        Return the status for the task holder.
        """
        return self.__status

    def addTag(self, name, value):
        """
        Add a tag to the task holder.
        """
        self.__tags[name] = value

    def hasTag(self, name):
        """
        Return a boolean telling if the input tag is defined.
        """
        return name in self.tagNames()

    def tagNames(self):
        """
        Return a list of tag names.
        """
        return self.__tags.keys()

    def tag(self, name, defaultValue=__sentinelValue):
        """
        Return the value for tag.
        """
        if name not in self.__tags:
            if defaultValue is self.__sentinelValue:
                raise TaskHolderInvalidTagNameError(
                    'Invalid tag name "{0}'.format(
                        name
                    )
                )
            else:
                return defaultValue

        return self.__tags[name]

    def addVar(self, name, value, isContextVar=False):
        """
        Add a variable to the task holder.
        """
        if isContextVar:
            self.__contextVarNames.add(name)
        elif name in self.__contextVarNames:
            self.__contextVarNames.remove(name)

        self.__vars[name] = value

    def hasVar(self, name):
        """
        Return a boolean telling if the input element variable is defined.
        """
        return name in self.varNames()

    def varNames(self):
        """
        Return a list of variable names.
        """
        return self.__vars.keys()

    def var(self, name, defaultValue=__sentinelValue):
        """
        Return the value for the variable.
        """
        if name not in self.__vars:
            if defaultValue is self.__sentinelValue:
                raise TaskHolderInvalidVarNameError(
                    'Invalid variable name "{0}'.format(
                        name
                    )
                )
            else:
                return defaultValue

        return self.__vars[name]

    def contextVarNames(self):
        """
        Return a list of variable names defined as context variables.
        """
        return list(self.__contextVarNames)

    def taskWrapper(self):
        """
        Return the task wrapper used to execute the task.
        """
        return self.__taskWrapper

    def targetTemplate(self):
        """
        Return the target template associated with the task holder.
        """
        return self.__targetTemplate

    def filterTemplate(self):
        """
        Return the filter template associated with the task holder.
        """
        return self.__filterTemplate

    def exportTemplate(self):
        """
        Return the export template associated with the task holder.
        """
        return self.__exportTemplate

    def importTemplates(self):
        """
        Return a list of templates used to import elements during run.
        """
        return self.__importTemplates

    def profileTemplate(self):
        """
        Return the profile template associated with the task holder.
        """
        return self.__profileTemplate

    def setTask(self, task):
        """
        Associate a cloned task with the task holder.
        """
        assert isinstance(task, Task), \
            "Invalid Task type"

        self.__task = task.clone()

    def task(self):
        """
        Return the task associated with the task holder.
        """
        return self.__task

    def childTasks(self, registeredTaskType='*'):
        """
        Return all tasks held by the task holder (recursively).

        The registered task type supports fnmatch pattern. For instance, you can use
        it to change the options in a specific task type. Also, in case you have more
        than one task in the result for the same registered type you could use the
        task metadata to define an unique information in the particular task you
        want to modify then filtering the result based on that metadata
        information (task.hasMetadata).
        """
        result = []

        if fnmatch(self.task().type(), registeredTaskType):
            result.append(self.task())

        for subTaskHolder in self.subTaskHolders():
            result += subTaskHolder.childTasks(registeredTaskType)

        return result

    def fromTaskToTaskHolder(self, task):
        """
        Return the task holder for the input task.
        """
        if task is self.task():
            return self

        for subTaskHolder in self.subTaskHolders():
            result = subTaskHolder.fromTaskToTaskHolder(task)
            if result:
                return result

        return None

    def addImportTemplate(self, template):
        """
        Add a template used to load elements exported by the export template.

        The elements are loaded during run.
        """
        assert isinstance(template, Template), "Invalid Template type!"

        self.__importTemplates.append(template)

    def addElements(self, elements, addTaskHolderVars=True):
        """
        Add a list of elements to the task.

        The elements are added to the task using "query" method to resolve
        the target template.
        """
        for element, filePath in self.query(elements).items():

            if addTaskHolderVars:
                # cloning element so we can modify it safely
                element = element.clone()

                for tagName in self.tagNames():

                    # in case the tag has already been
                    # defined in the element we skip it
                    if tagName in element.tagNames():
                        continue

                    element.setTag(
                        tagName,
                        self.tag(tagName)
                    )

                for varName in self.varNames():

                    # in case the variable has already been
                    # defined in the element we skip it
                    if varName in element.varNames():
                        continue

                    element.setVar(
                        varName,
                        self.var(varName),
                        varName in self.contextVarNames()
                    )

            self.__task.add(
                element,
                filePath
            )

    def matcher(self):
        """
        Return the element matcher associated with the task holder.
        """
        return self.__matcher

    def addSubTaskHolder(self, taskHolder):
        """
        Add a subtask holder with the current holder.
        """
        assert isinstance(taskHolder, TaskHolder), \
            "Invalid Task Holder Type"

        self.__subTaskHolders.append(taskHolder)

    def subTaskHolders(self):
        """
        Return a list sub task holders associated with the task holder.
        """
        return list(self.__subTaskHolders)

    def cleanSubTaskHolders(self):
        """
        Remove all sub task holders from the current task holder.
        """
        del self.__subTaskHolders[:]

    def query(self, elements):
        """
        Return a dict containing the matched element as key and resolved template as value.
        """
        validElements = {}
        for element in elements:
            if self.matcher().match(element):
                filterTemplateValue = self.filterTemplate().valueFromElement(element, self.__vars)

                # if the value of the filter is 0 or false the element is ignored
                if str(filterTemplateValue).lower() in ['false', '0']:
                    continue

                validElements[element] = self.targetTemplate().valueFromElement(element, self.__vars)

        # sorting result
        result = OrderedDict()
        for element, filePath in sorted(validElements.items(), key=lambda x: (x[1], x[0].var('fullPath'))):
            result[element] = filePath

        return result

    def toJson(self, includeSubTaskHolders=True):
        """
        Bake the current task holder (including all sub task holders) to json.
        """
        return json.dumps(
            self.__bakeTaskHolder(self, includeSubTaskHolders),
            indent=4,
            separators=(',', ': ')
        )

    def clone(self, includeSubTaskHolders=True):
        """
        Return a cloned instance of the current task holder.
        """
        return self.createFromJson(self.toJson(includeSubTaskHolders))

    def run(self, elements=[], ignoreImports=False):
        """
        Perform the task.

        Return all the elements resulted by the execution of the task (and sub tasks).
        """
        assert isinstance(elements, (tuple, list)), "Invalid element list!"

        useElements = list(elements)
        if not ignoreImports:
            for importTemplate in self.importTemplates():
                importFilePath = importTemplate.value(self.__vars)

                # loading elements
                with open(importFilePath) as f:
                    for elementJson in json.load(f):
                        element = Element.createFromJson(elementJson)

                        # the imported elements need to be validated
                        # by the element matcher
                        if self.matcher().match(element):
                            useElements.append(element)

        return self.__recursiveTaskRunner(
            self.clone(),
            useElements
        )

    @classmethod
    def createFromJson(cls, jsonContents):
        """
        Create a new task holder instance from json.
        """
        contents = json.loads(jsonContents)

        return cls.__loadTaskHolder(contents)

    def __setMatcher(self, matcher):
        """
        Associate a element matcher with the task holder.
        """
        assert isinstance(matcher, Matcher), \
            "Invalid Matcher type"
        self.__matcher = matcher

    def __setTargetTemplate(self, targetTemplate):
        """
        Associate a target template with the task holder.
        """
        assert isinstance(targetTemplate, Template), \
            "Invalid template type"

        self.__targetTemplate = targetTemplate

    def __setFilterTemplate(self, filterTemplate):
        """
        Associate a filter template with the task holder.

        A filter template can be used to filter out elements based on
        returning 0 or false as result of the filter.
        """
        assert isinstance(filterTemplate, Template), \
            "Invalid template type"

        self.__filterTemplate = filterTemplate

    def __setExportTemplate(self, exportTemplate):
        """
        Associate an export template with the task holder.

        This template is used to export the elements
        resulted by the task through "TaskHolder.run()"
        to a json file. This template represents of
        path for that json file.
        """
        assert isinstance(exportTemplate, Template), \
            "Invalid template type"

        self.__exportTemplate = exportTemplate

    def __setProfileTemplate(self, profileTemplate):
        """
        Associate a profile template with the task holder.

        This template is used to export a profile image that
        visualizes the execution of a task. When a path is
        specified in the template, it saves a PNG image that
        captures the profiled execution.
        """
        assert isinstance(profileTemplate, Template), \
            "Invalid template type"

        self.__profileTemplate = profileTemplate

    def __setTaskWrapper(self, taskWrapper):
        """
        Override the default task wrapper.
        """
        assert isinstance(taskWrapper, TaskWrapper), "Invalid taskWrapper type!"

        self.__taskWrapper = taskWrapper

    @classmethod
    def __bakeTaskHolder(cls, taskHolder, includeSubTaskHolders=True):
        """
        Auxiliary method to bake the task holder recursively.
        """
        # template info
        targetTemplate = taskHolder.targetTemplate().inputString()
        filterTemplate = taskHolder.filterTemplate().inputString()
        exportTemplate = taskHolder.exportTemplate().inputString()
        profileTemplate = taskHolder.profileTemplate().inputString()
        importTemplates = list(map(lambda x: x.inputString(), taskHolder.importTemplates()))

        taskHolderVars = {}
        for varName in taskHolder.varNames():
            taskHolderVars[varName] = taskHolder.var(varName)

        taskHolderTags = {}
        for tagName in taskHolder.tagNames():
            taskHolderTags[tagName] = taskHolder.tag(tagName)

        output = {
            'template': {
                'target': targetTemplate,
                'filter': filterTemplate,
                'export': exportTemplate,
                'import': importTemplates,
                'profile': profileTemplate
            },
            'vars': taskHolderVars,
            'tags': taskHolderTags,
            'status': taskHolder.status(),
            'contextVarNames': taskHolder.contextVarNames(),
            'regroupTag': taskHolder.regroupTag(),
            'task': taskHolder.task().toJson(),
            'subTaskHolders': []
        }

        if includeSubTaskHolders:
            output['subTaskHolders'] = list(map(cls.__bakeTaskHolder, taskHolder.subTaskHolders()))

        return output

    @classmethod
    def __loadTaskHolder(cls, taskHolderContents):
        """
        Auxiliary method used to load the contents of the task holder recursively.
        """
        # creating task holder
        targetTemplate = Template(taskHolderContents['template']['target'])
        filterTemplate = Template(taskHolderContents['template']['filter'])
        exportTemplate = Template(taskHolderContents['template']['export'])
        profileTemplate = Template(taskHolderContents['template']['profile'])
        importTemplates = taskHolderContents['template']['import']
        regroupTag = taskHolderContents.get('regroupTag', '')

        # creating task
        task = Task.createFromJson(taskHolderContents['task'])

        # building the task holder instance
        taskHolder = TaskHolder(
            task,
            targetTemplate,
            filterTemplate,
            exportTemplate,
            profileTemplate
        )

        # setting regroup tag
        taskHolder.setRegroupTag(regroupTag)

        # loading import templates
        for importTemplate in importTemplates:
            taskHolder.addImportTemplate(
                Template(importTemplate)
            )

        # setting status
        taskHolder.setStatus(taskHolderContents['status'])

        # adding vars
        contextVarNames = taskHolderContents['contextVarNames']
        for varName, varValue in taskHolderContents['vars'].items():
            taskHolder.addVar(
                varName,
                varValue,
                varName in contextVarNames
            )

        # adding tags
        for tagName, tagValue in taskHolderContents['tags'].items():
            taskHolder.addTag(
                tagName,
                tagValue
            )

        # adding sub task holders
        for subTaskHolderContent in taskHolderContents['subTaskHolders']:
            taskHolder.addSubTaskHolder(cls.__loadTaskHolder(subTaskHolderContent))

        return taskHolder

    @classmethod
    def __recursiveTaskRunner(cls, taskHolder, elements):
        """
        Perform the task runner recursively.
        """
        # when re-group tag is defined we get the input elements and regroup
        # them. This is going to split the processing of the task per group
        if taskHolder.regroupTag():
            result = []
            groupElements = Element.group(elements, taskHolder.regroupTag())
            for group in groupElements:
                newTaskHolder = taskHolder.clone()
                newTaskHolder.setRegroupTag('')
                result.extend(
                    cls.__recursiveTaskRunner(
                        newTaskHolder,
                        group
                    )
                )
            return result

        taskHolder.addElements(elements)
        result = []
        taskHolderVars = {}
        for varName in taskHolder.varNames():
            taskHolderVars[varName] = taskHolder.var(varName)

        # ignoring the execution of the task
        if taskHolder.status() == 'ignore' or not taskHolder.task().elements():
            pass

        # bypassing task execution
        elif taskHolder.status() == 'bypass':
            taskElements = taskHolder.task().elements()
            result += taskElements

        # running task through the wrapper
        else:
            profileTemplate = taskHolder.profileTemplate().value(taskHolderVars)
            if profileTemplate:
                profileOutput = pathlib.Path(profileTemplate).as_posix()

                if os.path.isdir(profileOutput):
                    profileOutput += '/profile'

                # including the extension in case it has not been defined
                if not profileOutput.lower().endswith('.png'):
                    profileOutput += '.png'

                taskHolder.task().setMetadata('output.profile', profileOutput)

            taskElements = taskHolder.taskWrapper().run(taskHolder.task())
            result += taskElements

        # exporting the result when export template is defined
        if taskHolder.exportTemplate().inputString():

            # processing template
            exportTemplate = taskHolder.exportTemplate().value(taskHolderVars)

            # writing elements
            if exportTemplate:
                try:
                    os.makedirs(os.path.dirname(exportTemplate))
                except OSError:
                    pass

                with open(exportTemplate, 'w') as f:
                    f.write(json.dumps(list(map(lambda x: x.toJson(), result))))

        # nothing to be done
        if taskHolder.status() == 'ignore' or not taskHolder.task().elements():
            return []

        # calling subtask holders
        for subTaskHolder in taskHolder.subTaskHolders():
            result += cls.__recursiveTaskRunner(subTaskHolder, taskElements)

        return result

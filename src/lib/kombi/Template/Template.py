import re
import os
import uuid
from ..Crawler import CrawlerInvalidVarError

class TemplateError(Exception):
    """Template error."""

class TemplateVarNotFoundError(TemplateError):
    """Template variable not found error."""

class TemplateVarCircularReferenceError(TemplateError):
    """Template variable circular reference error."""

class TemplateRequiredPathNotFoundError(TemplateError):
    """Required required path not found error."""

class TemplateProcedureNotFoundError(TemplateError):
    """Template procedure not found error."""

class Template(object):
    """
    Creates a template object based on a string defined using template syntax.

    A template string can contain crawler variables using the syntax
    {crawlerVariable}. Procedures can be used through the syntax (myprocedure),
    arguments can be passed to procedures after the procedure name,
    for instance (myprocedure {crawlerVariable}) where the arguments must be
    separated by space:
        "/tmp/{myVariable}/(myprocedure {myVariable} 'second arg' 3)"

    It supports calling procedures from inside of procedures. For instance:
        "/tmp/{myVariable}/(myprocedure (nestedprocedure {myVariable}) 'second arg' 3)"

    Arithmetic operations are supported like procedures using the syntax (4 + 1), for instance:
        "/tmp/(2 + 3)/({width} + 10 as <finalwidth>)/file_<finalwidth>.exr"

    Also, template engine provides special tokens designed specially to help with
    path manipulation:

    /! - Means the directory must exist for instance:
        "{prefix}/!shouldExist/{width}X{height}/{name}.(pad {frame} 10).{ext}"

    <parent> - Passes the computed parent path to a procedure. Keep in mind this
    is only supported by template procedures.
        "{prefix}/testing/(newver <parent>)/{name}.(pad {frame} 10).{ext}"

    <mytoken> - You can assign the result of a procedure to a token that can be used
    after the procedure in any part of the template by using the syntax
    "(someprocedure as <mytoken>)" in the last of the procedure:
        "{prefix}/testing/(newver <parent> as <version>)/{name}_<version>.(pad {frame} 10).{ext}"
    """

    __argsGroupRegex = r"'(?:''|[^']+)'|(?:[^' ]+)"
    __arithmeticOperatorsRegex = r"^[0-9+\-*\/\.'(\)]*$"
    __registeredProcedures = {}

    def __init__(self, inputString=""):
        """
        Create a template object.
        """
        self.setInputString(inputString)
        self.__setVarNames()
        self.__procedureValueCache = {}

    def inputString(self):
        """
        Return the raw template string used to create the object.
        """
        return self.__inputString

    def setInputString(self, inputString):
        """
        Set the template string.
        """
        assert isinstance(inputString, str), \
            "Invalid template string!"

        self.__inputString = inputString

    def varNames(self):
        """
        Return a list of variable names found in the input string.
        """
        return self.__varNames

    def valueFromCrawler(self, crawler, extraVars={}):
        """
        Return the value of the template based on a crawler.
        """
        allVars = {}
        for varName in self.varNames():
            if varName in extraVars:
                allVars[varName] = extraVars[varName]
            else:
                try:
                    allVars[varName] = crawler.var(varName)
                except CrawlerInvalidVarError:

                    # in case any information about the config
                    # is available including them
                    contextConfig = ''
                    if 'contextConfig' in extraVars:
                        contextConfig = extraVars['contextConfig']
                    elif 'contextConfig' in self.varNames():
                        contextConfig = crawler.var('contextConfig')
                    if contextConfig:
                        contextConfig = ' by the config "{}"'.format(contextConfig)

                    raise TemplateVarNotFoundError(
                        'Could not find variable "{}" for template "{}"{}'.format(
                            varName,
                            self.__inputString,
                            contextConfig
                        )
                    )

        return self.value(allVars)

    def value(self, crawlerVars={}):
        """
        Return the value of the template based on the input variables.
        """
        assert isinstance(crawlerVars, dict), "invalid crawlerVars type!"

        # converting the crawler values to string
        templateCrawlerVars = {}
        for key, value in crawlerVars.items():
            templateCrawlerVars[key] = '' if value is None else str(value)

        self.__validateTemplateVariables(templateCrawlerVars)

        # resolving variables values
        resolvedTemplate = self.inputString()

        # resolving function values
        finalResolvedTemplate = self.__resolveTemplate(
            resolvedTemplate,
            templateCrawlerVars
        )

        # resolving required path levels
        finalResolvedTemplate = self.__processTemplateRequiredLevels(finalResolvedTemplate)

        return finalResolvedTemplate

    @classmethod
    def registerProcedure(cls, name, procedureCallable):
        """
        Register a callable as procedure.
        """
        assert hasattr(procedureCallable, '__call__'), \
            "Invalid callable!"

        cls.__registeredProcedures[name] = procedureCallable

    @classmethod
    def registeredProcedureNames(cls):
        """
        Return a list of registered template procedures.
        """
        return cls.__registeredProcedures.keys()

    @classmethod
    def runProcedure(cls, procedureName, *args):
        """
        Run the procedure and return a value base on the args.
        """
        if procedureName not in cls.__registeredProcedures:
            raise TemplateProcedureNotFoundError(
                'Could not find procedure name: "{0}"'.format(
                    procedureName
                )
            )

        # executing procedure
        return str(cls.__registeredProcedures[procedureName](*args))

    @classmethod # noqa: C901
    def evalProcedure(cls, procedure, tokens=None):
        """
        Parse and run a procedure.

        A procedure must be a string describing the procedure name
        as first token and the arguments that should be passed to it
        separated by space, for instance:
            "(myProcedureA 'arg 1' arg2)"
            "(1 + 2)"

        You can call nested procedures by defining the procedures as
        as argument of the procedure you want to call the nested procedure.
        Make sure the nested proceures are surrounded by parentheses.
            "(myProcedureA 'arg 1' (myProcedureB 'arg 2' (myProcedureC 'arg 3')))"

        The arguments are always parsed as string, and they should be
        handled per procedure callable bases.
        """
        assert isinstance(procedure, str), \
            "Invalid procedure type!"

        assert procedure.startswith("(") and procedure.endswith(")"), \
            "Cannot parse procedure, it needs to be defined under: ()"

        procedure = procedure[1:-1]

        fullResolved = ''
        if tokens is None:
            tokens = {}

        for tokenName, tokenValue in tokens.items():
            procedure = procedure.replace(tokenName, tokenValue)

        insideProcedure = []
        insideQuote = False
        previousChar = None
        start = None
        for i, char in enumerate(procedure):

            if insideQuote and char == "'":
                if not insideProcedure:
                    fullResolved += char
                if previousChar != "\\":
                    insideQuote = False

            elif not insideQuote and char == "'":
                if not insideProcedure:
                    fullResolved += char
                insideQuote = True

            elif not insideQuote and char == '(':
                if char not in insideProcedure:
                    start = i
                insideProcedure.append(char)

            elif not insideQuote and char == ')':
                insideProcedure.pop()
                if not insideProcedure:
                    fullResolved += " '{}' ".format(
                        cls.evalProcedure(
                            procedure[start: i + 1],
                            tokens
                        ).replace("'", "\\'")
                    )

            elif len(insideProcedure) == 0:
                fullResolved += char

            previousChar = char

        procedure = fullResolved

        # executing arithmetic operations
        if re.match(cls.__arithmeticOperatorsRegex, procedure.replace(' ', '')):
            return str(int(eval(procedure.replace("'", ""))))

        # converting all the escaped single quoted to a special token
        singleQuoteId = cls.__generatePlaceHolderId()
        procedure = procedure.replace("\\'", singleQuoteId).strip()
        procedureName = procedure.split(' ')[0]
        procedureArgs = ' '.join(procedure.split(' ')[1:])

        assignResultToToken = None
        tokenAssignmentRegex = re.search(r" as <.*>(\s*|)$", procedureArgs.lower())
        if tokenAssignmentRegex:
            assignResultToToken = procedureArgs[tokenAssignmentRegex.start() + 4:].rstrip()
            procedureArgs = procedureArgs[:tokenAssignmentRegex.start()]

        rawArgs = re.findall(cls.__argsGroupRegex, procedureArgs)

        procedureArgs = list(map(lambda x: x[1:-1] if x.startswith("'") else x, rawArgs))

        # restoring single quoted to the arguments
        procedureArgs = list(map(lambda x: x.replace(singleQuoteId, "'"), procedureArgs))

        result = cls.runProcedure(
            procedureName,
            *procedureArgs
        )

        if assignResultToToken is not None:
            tokens[assignResultToToken] = result

        return result

    def __processTemplateRequiredLevels(self, finalResolvedTemplate):
        """
        Return a template string by processing the required levels.
        """
        if "/!" not in finalResolvedTemplate:
            return finalResolvedTemplate

        finalPath = []
        for pathLevel in finalResolvedTemplate.split('/'):
            if pathLevel.startswith("!"):
                finalPath.append(pathLevel[1:])
                resolvedPath = os.sep.join(finalPath)
                if not os.path.exists(resolvedPath):
                    raise TemplateRequiredPathNotFoundError(
                        'Template contains a path marked as required:\n"{0}"\n\nThis error is caused because the target path does not exist in the file system:\n{1}'.format(
                            pathLevel,
                            resolvedPath
                        )
                    )

            else:
                finalPath.append(pathLevel)
        return os.sep.join(finalPath)

    def __resolveTemplate(self, resolvedTemplate, crawlerVars):
        """
        Return a resolved template by processing all variables, tokens and procedures.
        """
        crawlerVars = self.__resolveVariables(crawlerVars)

        crawlerVarsEnclosing = dict(map(lambda x:  ('{' + x[0] + '}', x[1]), crawlerVars.items()))
        finalResolvedTemplate = ""
        tokens = {}
        requiredLevelToken = self.__generatePlaceHolderId()
        tokens[requiredLevelToken] = "/!"
        resolvedTemplate = resolvedTemplate.replace(tokens[requiredLevelToken], requiredLevelToken)

        for templatePart, isProcedure in self.__templateParts(resolvedTemplate):

            if isProcedure:
                endIndex = templatePart.rfind(')')
                assignResultToToken = None

                # processing the procedure only when it has not been
                # evaluated yet, otherwise return it from the cache.
                # Potentially we could add support for "((procedure))" rather
                # than "(procedure)" to tell to avoid this cache. However, the
                # default behaviour should be to always cache it (never change it)
                # otherwise it could side effect for instance in template procedures
                # that create new versions...
                rawTemplateProcedure = templatePart

                # checking of the result is going to be assigned to a token
                tokenAssignmentRegex = re.search(r" as <.*>(\s*|)$", rawTemplateProcedure.lower()[:-1])
                if tokenAssignmentRegex:
                    assignResultToToken = rawTemplateProcedure[tokenAssignmentRegex.start() + 4:-1].rstrip()
                    rawTemplateProcedure = rawTemplateProcedure[:tokenAssignmentRegex.start()] + ')'

                # this is a special token that allows to pass the parent path
                # to a procedure, replacing it with the parent path at this point.
                if not finalResolvedTemplate.endswith('/'):
                    tokens['<parent>'] = os.path.dirname(finalResolvedTemplate.replace("/!", "/"))
                else:
                    tokens['<parent>'] = finalResolvedTemplate.replace("/!", "/")

                # replacing token values
                templateLastPart = templatePart[endIndex + 1:]
                rawTemplateProcedure = self.__resolveData(
                    rawTemplateProcedure,
                    list(tokens.items()) + list(crawlerVarsEnclosing.items()),
                    procedure=True
                )

                if rawTemplateProcedure not in self.__procedureValueCache:
                    # replacing any reserved token from the result of the procedure
                    self.__procedureValueCache[rawTemplateProcedure] = self.evalProcedure(
                        rawTemplateProcedure
                    )

                procedureValue = self.__procedureValueCache[rawTemplateProcedure]
                if assignResultToToken:
                    tokens[assignResultToToken] = procedureValue
                    templateLastPart = templateLastPart.replace(assignResultToToken, procedureValue)

                templateLastPart = self.__resolveData(
                    templateLastPart,
                    list(tokens.items()) + list(crawlerVarsEnclosing.items())
                )
                finalResolvedTemplate += procedureValue + templateLastPart

            else:
                templatePart = self.__resolveData(
                    templatePart,
                    list(tokens.items()) + list(crawlerVarsEnclosing.items())
                )
                finalResolvedTemplate += templatePart

        return finalResolvedTemplate

    def __resolveVariables(self, crawlerVars):
        """
        Resolve crawler variables containing a value referencing another crawler variables.
        """
        crawlerVars = dict(crawlerVars)
        circularReferenceKeys = []
        unresolved = True
        while unresolved:
            unresolved = False
            for mainVarName, mainVarValue in crawlerVars.items():
                for currentVarName, currentVarValue in crawlerVars.items():

                    # ignoring same variable
                    if mainVarName == currentVarName:
                        continue

                    # checking if current value contains main variable name, if
                    # so we replace for the value
                    searchVarName = '{' + mainVarName + '}'
                    if searchVarName in currentVarValue:
                        circularReferenceKey = (mainVarName, currentVarName)

                        # checking for circular references
                        if circularReferenceKey in circularReferenceKeys:
                            raise TemplateVarCircularReferenceError(
                                'Found circular reference between the crawler variables: {{{0}}} and {{{1}}}'.format(
                                    circularReferenceKey[0],
                                    circularReferenceKey[1]
                                )
                            )
                        circularReferenceKeys.append(circularReferenceKey)

                        # replacing mainVariable name for its value
                        crawlerVars[currentVarName] = currentVarValue.replace(searchVarName, mainVarValue)

                        # restarting the process again until there is nothing left
                        # to be resolved
                        unresolved = True

        return crawlerVars

    def __resolveData(self, template, resultData, procedure=False):
        """
        Return a template by resolving all variables and tokens for the actual value.
        """
        placeHolders = {}
        for tokenName, tokenValue in resultData:
            tokenPlaceHolder = self.__generatePlaceHolderId()
            placeHolders[tokenPlaceHolder] = tokenValue.replace("'", "\\'") if procedure else tokenValue

            template = template.replace(
                tokenName,
                "'{}'".format(tokenPlaceHolder) if procedure else tokenPlaceHolder
            )

        # after creating an id of for each part that represents a variable or token we can
        # safely replace them for the real value. This is necessary to avoid
        # any variable that may contain a token name or even another variable name as result
        # to get their result also replaced
        for placeHolderId, placeHolderValue in placeHolders.items():
            template = template.replace(placeHolderId, placeHolderValue)

        return template

    def __validateTemplateVariables(self, crawlerVars):
        """
        Make sure the variables used by template are available, otherwise raise an exception (TemplateVarNotFoundError).
        """
        for requiredVarName in self.varNames():
            if requiredVarName not in crawlerVars:

                # in case any information about the config
                # is available including them
                contextConfig = ''
                if 'contextConfig' in crawlerVars:
                    contextConfig = ' by the config "{}"'.format(
                        crawlerVars['contextConfig']
                    )

                raise TemplateVarNotFoundError(
                    'Could not find a value for the variable "{}" for template "{}"{}'.format(
                        requiredVarName,
                        self.__inputString,
                        contextConfig
                    )
                )

    def __setVarNames(self):
        """
        Set the variable names found in the input template.
        """
        result = set()

        # detecting variables
        for templatePart in self.inputString().split("{"):
            if templatePart == '' or "}" not in templatePart:
                continue

            endIndex = templatePart.find('}')
            result.add(templatePart[:endIndex])

        self.__varNames = list(result)

    @classmethod # noqa: C901
    def __templateParts(cls, template):
        """
        Return list by splitting the template in parts.
        """
        parts = []
        inBetween = ''
        insideProcedure = []
        insideQuote = False
        previousChar = None
        start = None
        for i, char in enumerate(template):

            if insideQuote and char == "'":
                if previousChar != "\\":
                    insideQuote = False

            elif not insideQuote and char == "'":
                insideQuote = True

            elif not insideQuote and char == '(':
                if inBetween:
                    parts.append(
                        (inBetween, False)
                    )
                inBetween = ''
                if char not in insideProcedure:
                    start = i
                insideProcedure.append(char)

            elif not insideQuote and char == ')':
                insideProcedure.pop()
                if not insideProcedure:
                    parts.append(
                        (template[start: i + 1], True)
                    )

            elif not insideProcedure:
                inBetween += char

            previousChar = char

        if inBetween:
            parts.append(
                (inBetween, False)
            )

        return parts

    @classmethod
    def __generatePlaceHolderId(cls):
        """
        Return a unique id used for substitutions.
        """
        return '<value:{}>'.format(str(uuid.uuid4()))

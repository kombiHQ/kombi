import re
import os
import uuid
from .Crawler import CrawlerInvalidVarError

# compatibility with python 2/3
try:
    basestring
except NameError:
    basestring = str

class TemplateError(Exception):
    """Template error."""

class TemplateVarNotFoundError(TemplateError):
    """Template variable not found error."""

class TemplateRequiredPathNotFoundError(TemplateError):
    """Required required path not found error."""

class TemplateProcedureNotFoundError(TemplateError):
    """Template procedure not found error."""

class Template(object):
    """
    Creates a template object based on a string defined using template syntax.

    A template string can be represented using crawler variables using the syntax
    {crawlerVariable}. Procedures can be used through the syntax (myprocedure),
    arguments can be passed to procedures for instance (myprocedure {crawlerVariable})
    where the arguments must be separated by space like in bash:
        "/tmp/{myVariable}/(myprocedure {myVariable} 'second arg' 3)"

    Arithmetic operations are supported like procedures using the syntax (4 + 1), for instance:
        "/tmp/(2 + 3)/({width} + 10 as <finalwidth>)/file_<finalwidth>.exr"

    Also, template engine provides special tokens designed to help with
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
    __arithmeticOperatorsRegex = r"^[0-9+\-*\/\ \.'(\)]*$"
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
        assert isinstance(inputString, basestring), \
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

    @classmethod
    def evalProcedure(cls, procedure):
        """
        Parse and run a procedure.

        A procedure must be a string describing the procedure name
        as first token and the arguments that should be passed to it
        separated by space (aka bash), for instance:
            "myprocedure 'arg 1' arg2"
            "1 + 2"

        The arguments are always parsed as string, and they should be
        handled per procedure callable bases.
        """
        assert isinstance(procedure, basestring), \
            "Invalid procedure type!"

        # executing arithmetic operations
        if re.match(cls.__arithmeticOperatorsRegex, procedure):
            return str(int(eval(procedure.replace("'", ""))))

        # converting all the escaped single quoted to a special token
        singleQuoteId = cls.__generatePlaceHolderId()
        procedure = procedure.replace("\\'", singleQuoteId).strip()

        procedureName = procedure.split(' ')[0]
        rawArgs = re.findall(cls.__argsGroupRegex, ' '.join(procedure.split(' ')[1:]))
        procedureArgs = list(map(lambda x: x[1:-1] if x.startswith("'") else x, rawArgs))

        # restoring single quoted to the arguments
        procedureArgs = list(map(lambda x: x.replace(singleQuoteId, "'"), procedureArgs))

        return cls.runProcedure(procedureName, *procedureArgs)

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
        crawlerVarsEnclosing = dict(map(lambda x:  ('{' + x[0] + '}', x[1]), crawlerVars.items()))
        finalResolvedTemplate = ""
        tokens = {}
        requiredLevelToken = self.__generatePlaceHolderId()
        tokens[requiredLevelToken] = "/!"
        resolvedTemplate = resolvedTemplate.replace(tokens[requiredLevelToken], requiredLevelToken)

        for templatePart in resolvedTemplate.split("("):

            endIndex = templatePart.find(')')
            if endIndex != -1:
                assignResultToToken = None

                # processing the procedure only when it has not been
                # evaluated yet, otherwise return it from the cache.
                # Potentially we could add support for "((procedure))" rather
                # than "(procedure)" to tell to avoid this cache. However, the
                # default behaviour should be to always cache it (never change it)
                # otherwise it could side effect for instance in template procedures
                # that create new versions...
                rawTemplateProcedure = templatePart[:endIndex]

                # checking of the result is going to be assigned to a token
                tokenAssignmentRegex = re.search(r" as <.*>(\s*|)$", rawTemplateProcedure.lower())
                if tokenAssignmentRegex:
                    assignResultToToken = rawTemplateProcedure[tokenAssignmentRegex.start() + 4:].rstrip()
                    rawTemplateProcedure = rawTemplateProcedure[:tokenAssignmentRegex.start()]

                # this is a special token that allows to pass the parent path
                # to a procedure, replacing it with the parent path at this point.
                if not finalResolvedTemplate.endswith('/'):
                    tokens['<parent>'] = os.path.dirname(finalResolvedTemplate.replace(requiredLevelToken, "/"))
                else:
                    tokens['<parent>'] = finalResolvedTemplate.replace(requiredLevelToken, "/")

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
            if templatePart is '' or "}" not in templatePart:
                continue

            endIndex = templatePart.find('}')
            result.add(templatePart[:endIndex])

        self.__varNames = list(result)

    @classmethod
    def __generatePlaceHolderId(cls):
        """
        Return a unique id used for substitutions.
        """
        return '<value:{}>'.format(str(uuid.uuid4()))

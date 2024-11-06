import os
from collections import OrderedDict

class EnvModifierError(Exception):
    """Env modifier error."""

class EnvModifierInvalidVarError(EnvModifierError):
    """Env modifier invalid var error."""

class EnvModifierInvalidVarValueError(EnvModifierError):
    """Env modifier invalid var value error."""

class EnvModifier(object):
    """
    Creates a new modified environment.
    """

    def __init__(self, baseEnv={}):
        """
        Create an env modifier object.
        """
        self.__env = {
            'prepend': OrderedDict(),
            'append': OrderedDict(),
            'override': OrderedDict(),
            'unset': set()
        }

        self.__setBaseEnv(baseEnv)

    def baseEnv(self):
        """
        Return a dict containing the base environment used for modification.
        """
        return self.__baseEnv

    def addFromEnvModifier(self, envModifier):
        """
        Add the contents from another envModifier object.
        """
        assert isinstance(envModifier, EnvModifier), \
            "Invalid EnvModifier type!"

        # prepend
        for varName in envModifier.prependVarNames():
            self.addPrependVar(varName, envModifier.prependVar(varName))

        # append
        for varName in envModifier.appendVarNames():
            self.addAppendVar(varName, envModifier.appendVar(varName))

        # override
        for varName in envModifier.overrideVarNames():
            self.setOverrideVar(varName, envModifier.overrideVar(varName))

        # unset
        for varName in envModifier.unsetVarNames():
            self.addUnsetVar(varName)

    def addFromDict(self, inputDict):
        """
        Add the contents from a dict containing the vars inside of the operation type.

        The dictionary must follow the specification where the operation types
        should contain another dict with the environment variables, except from
        unset that expects a list of variable names. The operation types are
        (append, prepend, override and unset) and they can be optional:
        {
            "append": [
                "VAR_NAME": [
                    "VAR_VALUE"
                ]
            ],
            "prepend": [
                "VAR_NAME": [
                    "VAR_VALUE"
                ]
            ],
            "override": [
                "VAR_NAME": [
                    "VAR_VALUE"
                ]
            ],
            "unset": [
                "VAR_NAME"
            ]
        }
        """
        assert isinstance(inputDict, dict), \
            "Invalid dictionary!"

        # prepend
        if 'prepend' in inputDict:
            for envName, envValue in inputDict["prepend"].items():
                self.addPrependVar(envName, envValue)

        # append
        if 'append' in inputDict:
            for envName, envValue in inputDict["append"].items():
                self.addAppendVar(envName, envValue)

        # override
        if 'override' in inputDict:
            for envName, envValue in inputDict["override"].items():
                self.setOverrideVar(envName, envValue)

        # unset
        if 'unset' in inputDict:
            for envName in inputDict["unset"]:
                self.addUnsetVar(envName)

    def addPrependVar(self, name, value):
        """
        Add a value that is going to be prepended to the env.
        """
        if name not in self.__env['prepend']:
            self.__env['prepend'][name] = []

        if isinstance(value, list):
            self.__env['prepend'][name] = value + self.__env['prepend'][name]
        else:
            self.__env['prepend'][name].insert(0, value)

    def prependVar(self, name):
        """
        Return a list of values used by the prepend var.
        """
        if name not in self.__env['prepend']:
            raise EnvModifierInvalidVarError(
                'Invalid Variable "{0}"'.format(name)
            )

        return self.__env['prepend'][name]

    def prependVarNames(self):
        """
        Return a list of prepend var names.
        """
        return self.__env['prepend'].keys()

    def addAppendVar(self, name, value):
        """
        Add a value that is going to be appended to the env.
        """
        if name not in self.__env['append']:
            self.__env['append'][name] = []

        if isinstance(value, list):
            self.__env['append'][name] += value
        else:
            self.__env['append'][name].append(value)

    def appendVar(self, name):
        """
        Return a list of values used by the append var.
        """
        if name not in self.__env['append']:
            raise EnvModifierInvalidVarError(
                'Invalid Variable "{0}"'.format(name)
            )

        return self.__env['append'][name]

    def appendVarNames(self):
        """
        Return a list of append var names.
        """
        return self.__env['append'].keys()

    def setOverrideVar(self, name, value):
        """
        Set a variable value, use it when you want to override a variable.
        """
        self.__env['override'][name] = value

    def overrideVar(self, name):
        """
        Return the value that is going to be used to override the original value.
        """
        if name not in self.__env['override']:
            raise EnvModifierInvalidVarError(
                'Invalid Variable "{0}"'.format(name)
            )

        return self.__env['override'][name]

    def overrideVarNames(self):
        """
        Return a list of override var names.
        """
        return self.__env['override'].keys()

    def addUnsetVar(self, name):
        """
        Add a variable name that is going to be unset.
        """
        self.__env['unset'].add(name)

    def unsetVarNames(self):
        """
        Return a list of variables that are going to be unset.
        """
        return list(self.__env['unset'])

    def generate(self):
        """
        Return brand new environment based on the current configuration.
        """
        result = dict(self.baseEnv())

        self.__modifyPrependVars(result)
        self.__modifyAppendVars(result)
        self.__modifyOverrideVars(result)
        self.__modifyUnsetVars(result)

        return result

    def __modifyUnsetVars(self, env):
        """
        Modify in place the env by unseating the variables.
        """
        for varName in self.unsetVarNames():
            if varName in env:
                del env[varName]

    def __modifyOverrideVars(self, env):
        """
        Modify in place the env by overriding variables.
        """
        for varName in self.overrideVarNames():
            env[varName] = self.__convertEnvValue(
                self.overrideVar(varName)
            )

    def __modifyPrependVars(self, env):
        """
        Modify in place the env by prepending variables.
        """
        for varName in self.prependVarNames():
            convertedValue = self.__convertEnvValue(self.prependVar(varName))

            if varName in env and len(env[varName]):
                convertedValue = '{0}{1}{2}'.format(
                    convertedValue,
                    os.pathsep,
                    env[varName]
                )

            env[varName] = convertedValue

    def __modifyAppendVars(self, env):
        """
        Modify in place the env by appending variables.
        """
        for varName in self.appendVarNames():
            convertedValue = self.__convertEnvValue(self.appendVar(varName))

            if varName in env and len(env[varName]):
                convertedValue = '{2}{1}{0}'.format(
                    convertedValue,
                    os.pathsep,
                    env[varName]
                )

            env[varName] = convertedValue

    def __convertEnvValue(self, value):
        """
        Convert a value to an environment convention.
        """
        result = []

        if isinstance(value, str):
            result.append(value)
        elif isinstance(value, list):
            result = value
        else:
            raise EnvModifierInvalidVarValueError(
                'Could not convert value: "{0}"'.format(str(value))
            )

        # in case of performance deterioration, it may worth to
        # process all values in one go.
        for index, value in enumerate(result):
            result[index] = value

        return os.pathsep.join(map(str, result))

    def __setBaseEnv(self, env):
        """
        Set a dict with the base environment that should be used for modification.
        """
        self.__baseEnv = dict(env)

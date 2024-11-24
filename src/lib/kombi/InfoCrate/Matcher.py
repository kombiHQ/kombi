from fnmatch import fnmatch
from .InfoCrate import InfoCrate

class Matcher(object):
    """
    Utility class used to check if a infoCrate matches the types and variables.
    """

    def __init__(self, matchTypes=[], matchVars={}):
        """
        Create a infoCrate matcher object.
        """
        self.__setMatchTypes(matchTypes)
        self.__setMatchVars(matchVars)

    def matchTypes(self):
        """
        Return a list of infoCrate types used to match.
        """
        return self.__matchTypes

    def matchVarNames(self):
        """
        Return a list of variable names that should be used to match the infoCrate.
        """
        return self.__matchVars.keys()

    def matchVar(self, varName):
        """
        Return the variable value.
        """
        return self.__matchVars[varName]

    def match(self, infoCrate):
        """
        Return a boolean telling if the infoCrate matches.

        TODO: ideally it should be breakdown in two methods, so one that
        test and another one that actually throws an exception telling
        why it does not match.
        """
        assert isinstance(infoCrate, InfoCrate), \
            "Invalid infoCrate type!"

        if not self.__matchType(infoCrate.var('type'), infoCrate):
            return False

        for varName in self.matchVarNames():

            # when variable is belongs to exclusively to
            # a specific type
            varNameParts = varName.split('=')
            if len(varNameParts) > 1 and infoCrate.var('type') not in InfoCrate.registeredSubTypes(varNameParts[0]):
                continue

            # checking if variable is part of the infoCrate
            if varNameParts[-1] not in infoCrate.varNames():
                return False

            matchVarValue = self.matchVar(varName)

            # the value can be a list of possibilities
            if not isinstance(matchVarValue, (list, tuple)):
                matchVarValue = [matchVarValue]

            foundValue = False
            for value in matchVarValue:
                if fnmatch(str(infoCrate.var(varNameParts[-1])), str(value)):
                    foundValue = True
                    break

            if not foundValue:
                return False

        return True

    def __matchType(self, infoCrateType, infoCrate):
        """
        Return a boolean telling if the infoCrate match the type.
        """
        foundType = not self.matchTypes()
        for matchType in self.matchTypes():
            registeredTypes = InfoCrate.registeredSubTypes(matchType)
            if infoCrateType in registeredTypes:
                foundType = True
                break

        return foundType

    def __setMatchTypes(self, matchTypes):
        """
        Set a list of infoCrate types used to match.

        The types can be defined using glob syntax.
        """
        assert isinstance(matchTypes, list), \
            "Invalid list!"

        self.__matchTypes = list(matchTypes)

    def __setMatchVars(self, matchVars):
        """
        Set a list of variable names that should match in the infoCrate.

        The var values can be defined using glob syntax.
        """
        assert isinstance(matchVars, dict), \
            "Invalid dict!"

        self.__matchVars = dict(matchVars)

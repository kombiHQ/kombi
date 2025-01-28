from fnmatch import fnmatch
from .Element import Element

class Matcher(object):
    """
    Utility class used to check if a element matches the types and variables.
    """

    def __init__(self, matchTypes=[], matchVars={}):
        """
        Create a element matcher object.
        """
        self.__setMatchTypes(matchTypes)
        self.__setMatchVars(matchVars)

    def matchTypes(self):
        """
        Return a list of element types used to match.
        """
        return self.__matchTypes

    def matchVarNames(self):
        """
        Return a list of variable names that should be used to match the element.
        """
        return self.__matchVars.keys()

    def matchVar(self, varName):
        """
        Return the variable value.
        """
        return self.__matchVars[varName]

    def match(self, element):
        """
        Return a boolean telling if the element matches.

        TODO: ideally it should be breakdown in two methods, so one that
        test and another one that actually throws an exception telling
        why it does not match.
        """
        assert isinstance(element, Element), \
            "Invalid element type!"

        if not self.__matchType(element.var('type'), element):
            return False

        for varName in self.matchVarNames():

            # when var exclusively belongs to a specific type
            varNameParts = varName.split('=')
            if len(varNameParts) > 1 and element.var('type') not in Element.registeredSubTypes(varNameParts[0]):
                continue

            # checking if variable is part of the element
            if varNameParts[-1] not in element.varNames():
                return False

            matchVarValue = self.matchVar(varName)

            # the value can be a list of possibilities
            if not isinstance(matchVarValue, (list, tuple)):
                matchVarValue = [matchVarValue]

            foundValue = False
            for value in matchVarValue:
                if fnmatch(str(element.var(varNameParts[-1])), str(value)):
                    foundValue = True
                    break

            if not foundValue:
                return False

        return True

    def __matchType(self, elementType, element):
        """
        Return a boolean telling if the element match the type.
        """
        foundType = not self.matchTypes()
        for matchType in self.matchTypes():
            registeredTypes = Element.registeredSubTypes(matchType)
            if elementType in registeredTypes:
                foundType = True
                break

        return foundType

    def __setMatchTypes(self, matchTypes):
        """
        Set a list of element types used to match.

        The types can be defined using glob syntax.
        """
        assert isinstance(matchTypes, list), \
            "Invalid list!"

        self.__matchTypes = list(matchTypes)

    def __setMatchVars(self, matchVars):
        """
        Set a list of variable names that should match in the element.

        The var values can be defined using glob syntax.
        """
        assert isinstance(matchVars, dict), \
            "Invalid dict!"

        self.__matchVars = dict(matchVars)

from collections import OrderedDict

class VarExtractorError(Exception):
    """
    Var Extractor Error.
    """

    def __init__(self, message, value, valuePattern, valueContextIndex=None, valuePatternContextIndex=None):
        """
        Create a var extractor exception.
        """
        super(VarExtractorError, self).__init__(message)

        self.__valueContextIndex = valueContextIndex
        self.__valuePatternContextIndex = valuePatternContextIndex
        self.__value = value
        self.__valuePattern = valuePattern

    def fullMessage(self):
        """
        Return a full message version containing details about the error.
        """
        raise NotImplementedError

    def value(self):
        """
        Return the value used during the error.
        """
        return self.__value

    def valuePattern(self):
        """
        Return the value pattern used during the error.
        """
        return self.__valuePattern

    def valuePatternContextIndex(self):
        """
        Return the value pattern char context index.
        """
        return self.__valuePatternContextIndex

    def valueContextIndex(self):
        """
        Return the value char context index.
        """
        return self.__valueContextIndex

class VarExtractorNotMatchingCharError(VarExtractorError):
    """
    Var Extractor Not Matching Char Error.
    """

    def fullMessage(self):
        """
        Return a full message version containing details about the error.
        """
        return "\n  {}:\n\n    {}\n    {}^  (expected)\n\n    {}\n    {}^  (found)\n".format(
            self.message,
            self.valuePattern(),
            "-" * self.valuePatternContextIndex(),
            self.value(),
            "-" * self.valueContextIndex()
        )

class VarExtractorMissingSeparatorError(VarExtractorError):
    """
    Var Extractor Missing Separator Error.
    """

    def fullMessage(self):
        """
        Return a full message version containing details about the error.
        """
        return "\n  {}:\n\n    {}\n    {}^  (found)".format(
            self.message,
            self.valuePattern(),
            "-" * self.valuePatternContextIndex()
        )

class VarExtractorCannotFindExpectedCharError(VarExtractorError):
    """
    Var Extractor Cannot Find Expected Char.
    """

    def fullMessage(self):
        """
        Return a full message version containing details about the error.
        """
        return "\n  {}:\n\n    {}\n    {}^  (expected)\n\n    {}\n    {}^  (can't find expected char after...)\n".format(
            self.message,
            self.valuePattern(),
            "-" * self.valuePatternContextIndex(),
            self.value(),
            "-" * self.valueContextIndex()
        )

class VarExtractor(object):
    """
    Utility class used to extract variables encoded in a string.

    The variables must be enclosed inside {<NAME>}, for instance: {myVar}

    {@myVar} - context variables can be defined using the prefix '@'

    {myVar:<SIZE>} - an optional fixed size for variable's value can be
    defined by assigning the size after the separator ":", for
    instance: {myVar:2}

    {myVar:2<TYPE>} or {myVar:<TYPE>} - By default values are represented
    as string. However, you can cast the value to a specific type by
    specifying the type as LAST character after ":", supported types:

        {myVar:i} - for a value converted to integer
        {myVar:f} - for a value converted to float
        {myVar:S} - for a value converted to uppercase string
        {myVar:s} - for a value converted to lowercase string

        You can use the type notation together with the fixed size notation
        by defining the type after the fixed size, for instance: {myVar:3i}

    # - This notation can be used to ignore a single character, for instance:
        value pattern: ABC_{myVar}.####.png
        value: ABC_DEF.0001.png

    * - This notation can be used to ignore all characters until the next
    character defined after '*' in the value pattern is found under the value
    (aka glob).
        value pattern: ABC_*_{myVar}.png
        value: ABC_THIS-SHOULD-BE-IGNORED_DEF.png


    EXAMPLE:
        Value:
            PRO_ABC_DEF_FOO_V0001.0001.png

        Value Pattern:
            {job:3}_{seq:3}_{shot:3}_{plateName}_V{@version:4i}.####.png

    You can use the method "VarExtractor.match()" to know if the extraction has
    been done successfully. For additional information about the match
    failure you can query the method "VarExtractor.error()" to retrieve the
    exception. Also, you can print(varExtractor) instance for debugging purposes.
    The printed version includes debugging information.
    """

    def __init__(self, value, valuePattern, raiseOnFail=False):
        """
        Create a var extractor object.
        """
        self.__value = value
        self.__valuePattern = valuePattern
        self.__vars = OrderedDict()
        self.__contextVarNames = []
        self.__error = None

        try:
            self.__extract()
        except VarExtractorError as err:
            if raiseOnFail:
                raise err
            self.__error = err

    def match(self):
        """
        Return a boolean telling if the variables have been extracted successfully.
        """
        return (self.__error is None)

    def varNames(self):
        """
        Return a list of variable names.
        """
        return list(self.__vars.keys())

    def var(self, varName):
        """
        Return the value of the variable name.
        """
        return self.__vars[varName]

    def value(self):
        """
        Return the raw value.
        """
        return self.__value

    def contextVarNames(self):
        """
        Return a list of variable names that are defined as context variables.
        """
        return list(self.__contextVarNames)

    def error(self):
        """
        Return the exception associated when the failure during the match.
        """
        return self.__error

    def valuePattern(self):
        """
        Return the value pattern.
        """
        return self.__valuePattern

    def __repr__(self):
        """
        Return a string representation for the var extractor.
        """
        content = []
        for varName, varValue in self.__vars.items():
            content.append("{}={}".format(
                varName, varValue)
            )

        return "{}(match:{})[{}]{}".format(
            self.__class__.__name__,
            self.__error is None,
            ", ".join(content),
            "" if self.__error is None else self.__error.fullMessage()
        )

    def __extract(self):
        """
        Perform the extraction of the variables.
        """
        currentVar = ''
        insideVar = False
        valueCurrentIndex = 0
        for index, char in enumerate(self.__valuePattern):

            # detecting var
            if char == '{':
                insideVar = True

            # handling var
            elif char == '}':
                insideVar = False
                valueCurrentIndex = self.__processVar(
                    currentVar,
                    index,
                    valueCurrentIndex
                )
                currentVar = ''

            # extracting var name
            elif insideVar:
                currentVar += char

            # handling glob
            elif char == '*':
                if index + 1 < len(self.__valuePattern):
                    skipUntil = self.__valuePattern[index + 1]
                    if skipUntil == '{':
                        raise VarExtractorMissingSeparatorError(
                            'Missing separator between glob and var',
                            self.__value,
                            self.__valuePattern,
                            valueCurrentIndex,
                            index + 1
                        )

                    nextValueIndex = self.__value[valueCurrentIndex:].find(skipUntil)

                    if nextValueIndex == -1:
                        raise VarExtractorCannotFindExpectedCharError(
                            'Cannot find char after glob',
                            self.__value,
                            self.__valuePattern,
                            valueCurrentIndex,
                            index + 1
                        )

                    valueCurrentIndex += nextValueIndex
                else:
                    break

            elif valueCurrentIndex >= len(self.__value) or char != self.__value[valueCurrentIndex] and char != "#":
                raise VarExtractorNotMatchingCharError(
                    "Cannot match char",
                    self.__value,
                    self.__valuePattern,
                    valueCurrentIndex,
                    index
                )

            else:
                valueCurrentIndex += 1

    def __processVar(self, currentVar, index, valueCurrentIndex):
        """
        Assign the variable value and return a new index for the current value.
        """
        currentVar = currentVar.split(':')
        varValueSize = 0
        valueType = ''

        # extracting the optional value type. This is defined after the optional
        # variable size, for instance {name:2f}
        if len(currentVar) > 1 and not currentVar[1].isdigit():
            valueType = currentVar[1][-1]
            # now we have extracted the type we remove it from
            # the current var for further processing.
            currentVar[1] = currentVar[1][:-1]

        # checking if the optional value size is defined
        if len(currentVar) > 1 and currentVar[1].isdigit():
            varValueSize = int(currentVar[1])

        # when value size is not defined, computing it
        else:
            partialValue = self.__value[valueCurrentIndex:]

            if index + 1 < len(self.__valuePattern):
                nextChar = self.__valuePattern[index + 1]
                nextValueIndex = partialValue.find(nextChar)

                if not nextValueIndex:
                    raise VarExtractorCannotFindExpectedCharError(
                        'Cannot find char after var name {}'.format(currentVar[0]),
                        self.__value,
                        self.__valuePattern,
                        nextChar,
                        len(self.__value)
                    )
            else:
                nextValueIndex = len(partialValue)

            varValueSize = len(self.__value[valueCurrentIndex: valueCurrentIndex + nextValueIndex])

        # processing final value
        finalValue = self.__toValue(
            valueType,
            self.__value[valueCurrentIndex: valueCurrentIndex + varValueSize],
            index,
            valueCurrentIndex + varValueSize - 1,
        )

        # handling context variable
        if currentVar[0].startswith('@'):
            currentVar[0] = currentVar[0][1:]
            self.__contextVarNames.append(currentVar[0])

        # assigning variable
        self.__vars[currentVar[0]] = finalValue
        valueCurrentIndex += varValueSize

        return valueCurrentIndex

    def __toValue(self, valueType, value, index, valueIndex):
        """
        Return the value for the variable.
        """
        if valueType.lower() in ('i', 'f'):
            result = None
            try:
                if valueType.lower() == 'i':
                    result = int(value)
                else:
                    result = float(value)
            except ValueError:
                raise VarExtractorNotMatchingCharError(
                    "Cannot cast value '{}' to numeric value".format(value),
                    self.__value,
                    self.__valuePattern,
                    valueIndex,
                    index
                )
            return result
        elif valueType == 'S':
            return value.upper()
        elif valueType == 's':
            return value.lower()
        return value

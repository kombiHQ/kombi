from Qt import QtWidgets, QtCore

class OptionVisual(QtWidgets.QWidget):
    """
    This class contains an interface to create the widgets used by the options.
    """

    valueChanged = QtCore.Signal(object)
    __registeredOptionVisuals = {}
    __registeredFallbackDefaultVisuals = {}
    __registeredOptionVisualExamples = {}

    def __init__(self, optionName, optionValue, uiHints=None):
        """
        Create an OptionVisual object.
        """
        super().__init__()

        self.__setOptionName(optionName)
        self.__setOptionValue(optionValue)
        self.__setUIHint(uiHints or {})

        # in case a custom style sheet has been defined for the option
        if 'styleSheet' in self.uiHints():
            self.setStyleSheet(self.uiHints()['styleSheet'])

    def reset(self):
        """
        For re-implementation: This method is invoked after the valueChanged signal has been connected.

        At this point, it is safe to emit the valueChanged signal. This is useful when you need to
        change the value during the initialization of the option visual.
        """

    def uiHints(self):
        """
        Return a dict containing all the UI hints associated with the visual.
        """
        return self.__uiHints

    def optionName(self):
        """
        Return the option name assigned to the visual during the creation.
        """
        return self.__optionName

    def optionValue(self):
        """
        Return the option value assigned to the visual during the creation.
        """
        return self.__optionValue

    def __setUIHint(self, uiHints):
        """
        Set all ui hints associated with the visual.
        """
        assert isinstance(uiHints, dict), "Invalid uiHint type!"

        self.__uiHints = uiHints

    def __setOptionName(self, optionName):
        """
        Set the option name.
        """
        assert isinstance(optionName, str), "option name needs to be defined as string!"

        self.__optionName = optionName

    def __setOptionValue(self, optionValue):
        """
        Set the option value.
        """
        self.__optionValue = optionValue

    @classmethod
    def create(cls, optionName, optionValue, uiHints=None):
        """
        Factory an option visual widget.

        In case the visual is not defined under the uiHints dict. It will use a fallback widget.
        """
        registeredName = None
        if uiHints is not None and 'visual' in uiHints:
            registeredName = uiHints['visual']

        if not registeredName and optionValue is None:
            registeredName = 'null'

        if registeredName is None:
            for valueType, fallbackRegisteredName in reversed(list(cls.__registeredFallbackDefaultVisuals.items())):
                if isinstance(optionValue, valueType):
                    registeredName = fallbackRegisteredName
                    break
        assert registeredName, f"Value '{optionValue}' for option '{optionName}' is not supported!"

        optionVisual = cls.__registeredOptionVisuals[registeredName](
            optionName,
            optionValue,
            uiHints
        )

        optionVisual.reset()

        return optionVisual

    @classmethod
    def createExample(cls, registeredOptionVisualName, registeredExampleName):
        """
        Factory an option visual widget example.
        """
        assert registeredOptionVisualName in cls.__registeredOptionVisualExamples, \
            'No examples are registered for: {}'.format(registeredOptionVisualName)
        assert registeredExampleName in cls.__registeredOptionVisualExamples[registeredOptionVisualName], \
            'Invalid registered example name: {}'.format(registeredExampleName)

        exampleData = cls.__registeredOptionVisualExamples[registeredOptionVisualName][registeredExampleName]

        uiHints = {}
        if exampleData['uiHints'] is not None:
            uiHints = dict(exampleData['uiHints'])
        uiHints['visual'] = registeredOptionVisualName

        return cls.create('example', exampleData['value'], uiHints)

    @classmethod
    def registeredNames(cls):
        """
        Return all registered names.
        """
        return cls.__registeredOptionVisuals

    @classmethod
    def registerFallbackDefaultVisual(cls, registeredName, valueType):
        """
        Register a fallback default visual which is used when the visual is not defined under the uiHints.
        """
        assert isinstance(registeredName, str), 'Invalid registeredName str type'
        assert registeredName in cls.__registeredOptionVisuals, 'Invalid Option Visual (not registered): {}'.format(registeredName)
        cls.__registeredFallbackDefaultVisuals[valueType] = registeredName

    @classmethod
    def registeredExampleNames(cls, registeredOptionVisualName):
        """
        Return a list of example names registered for the input option visual class.
        """
        assert registeredOptionVisualName in cls.__registeredOptionVisuals, \
            'Invalid registered name: {}'.format(registeredOptionVisualName)
        if registeredOptionVisualName not in cls.__registeredOptionVisualExamples:
            return []
        return cls.__registeredOptionVisualExamples[registeredOptionVisualName].keys()

    @classmethod
    def registerExample(cls, registeredOptionVisualName, exampleName, value, uiHints=None):
        """
        Register an example based on the input exampleName for the option visual.
        """
        assert isinstance(exampleName, str), 'Invalid example name str type'
        assert registeredOptionVisualName in cls.__registeredOptionVisuals, \
            'Invalid registered name: {}'.format(registeredOptionVisualName)

        if registeredOptionVisualName not in cls.__registeredOptionVisualExamples:
            cls.__registeredOptionVisualExamples[registeredOptionVisualName] = {}

        cls.__registeredOptionVisualExamples[registeredOptionVisualName][exampleName] = {
            'value': value,
            'uiHints': uiHints
        }

    @classmethod
    def register(cls, name, optionVisualClass):
        """
        Register a option visual class.
        """
        assert isinstance(name, str), 'Invalid name str type'
        assert issubclass(optionVisualClass, OptionVisual), 'Invalid Option Visual Type'

        cls.__registeredOptionVisuals[name] = optionVisualClass

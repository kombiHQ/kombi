from Qt import QtWidgets, QtCore

class OptionVisual(QtWidgets.QWidget):
    """
    This class contains an interface to create the widgets used by the options.
    """

    valueChanged = QtCore.Signal(object)
    __registeredOptionVisuals = {}
    __registeredFallbackDefaultVisuals = {}

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
            for valueType, fallbackRegisteredName in reversed(cls.__registeredFallbackDefaultVisuals.items()):
                if isinstance(optionValue, valueType):
                    registeredName = fallbackRegisteredName
                    break
        assert registeredName, f"Value '{optionValue}' for option '{optionName}' is not supported!"

        return cls.__registeredOptionVisuals[registeredName](
            optionName,
            optionValue,
            uiHints
        )

    @classmethod
    def registeredNames(cls):
        """
        Return all registered names.
        """
        return cls.__registeredOptionVisuals

    @classmethod
    def registerFallbackDefaultVisual(cls, valueType, name):
        """
        Register a fallback default visual which is used when the visual is not defined under the uiHints.
        """
        assert isinstance(name, str), 'Invalid name str type'
        assert name in cls.__registeredOptionVisuals, 'Invalid Option Visual (not registered): {}'.format(name)
        cls.__registeredFallbackDefaultVisuals[valueType] = name

    @classmethod
    def register(cls, name, optionVisualClass):
        """
        Register a option visual class.
        """
        assert isinstance(name, str), 'Invalid name str type'
        assert issubclass(optionVisualClass, OptionVisual), 'Invalid Option Visual Type'

        cls.__registeredOptionVisuals[name] = optionVisualClass

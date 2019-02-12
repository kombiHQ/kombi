import operator
from ..Template import Template

class _Math(object):
    """
    Basic math functions.

    The arithmetic operations can be done directly through
    the operator support. For instance:
    (4 + 4) same as (sum 4 4)
    """

    @staticmethod
    def sumInt(*args):
        """
        Sum (cast to integer).
        """
        intArgs = _Math.__castToInt(*args)
        return int(operator.add(
            intArgs[0],
            intArgs[1]
        ))

    @staticmethod
    def subtractInt(*args):
        """
        Subtraction (cast to integer).
        """
        intArgs = _Math.__castToInt(*args)
        return int(operator.sub(
            intArgs[0],
            intArgs[1]
        ))

    @staticmethod
    def multiplyInt(*args):
        """
        Multiply (cast to integer).
        """
        intArgs = _Math.__castToInt(*args)
        return int(operator.mul(
            intArgs[0],
            intArgs[1]
        ))

    @staticmethod
    def divideInt(*args):
        """
        Divide (cast to integer).
        """
        intArgs = _Math.__castToInt(*args)
        return int(operator.truediv(
            intArgs[0],
            intArgs[1]
        ))

    @staticmethod
    def minimumInt(*args):
        """
        Minimum (cast to integer).
        """
        intArgs = _Math.__castToInt(*args)
        return int(min(
            intArgs[0],
            intArgs[1]
        ))

    @staticmethod
    def maximumInt(*args):
        """
        Maximum (cast to integer).
        """
        intArgs = _Math.__castToInt(*args)
        return int(max(
            intArgs[0],
            intArgs[1]
        ))

    @staticmethod
    def __castToInt(*args):
        """
        Cast the input args to int.
        """
        return list(map(int, args))


# sum
Template.registerProcedure(
    'sum',
    _Math.sumInt
)

# subtraction
Template.registerProcedure(
    'sub',
    _Math.subtractInt
)

# multiply
Template.registerProcedure(
    'mult',
    _Math.multiplyInt
)

# divide
Template.registerProcedure(
    'div',
    _Math.divideInt
)

# minimum
Template.registerProcedure(
    'min',
    _Math.minimumInt
)

# maximum
Template.registerProcedure(
    'max',
    _Math.maximumInt
)

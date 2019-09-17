"""
Basic math functions.

The arithmetic operations can be done directly through
the operator support. For instance:
(4 + 4) same as (sum 4 4)
"""

import operator
from ..Template import Template

def sumInt(*args):
    """
    Sum (cast to integer).
    """
    intArgs = __castToInt(*args)
    return int(operator.add(
        intArgs[0],
        intArgs[1]
    ))

def subtractInt(*args):
    """
    Subtraction (cast to integer).
    """
    intArgs = __castToInt(*args)
    return int(operator.sub(
        intArgs[0],
        intArgs[1]
    ))

def multiplyInt(*args):
    """
    Multiply (cast to integer).
    """
    intArgs = __castToInt(*args)
    return int(operator.mul(
        intArgs[0],
        intArgs[1]
    ))

def divideInt(*args):
    """
    Divide (cast to integer).
    """
    intArgs = __castToInt(*args)
    return int(operator.truediv(
        intArgs[0],
        intArgs[1]
    ))

def minimumInt(*args):
    """
    Minimum (cast to integer).
    """
    intArgs = __castToInt(*args)
    return int(min(
        intArgs[0],
        intArgs[1]
    ))

def maximumInt(*args):
    """
    Maximum (cast to integer).
    """
    intArgs = __castToInt(*args)
    return int(max(
        intArgs[0],
        intArgs[1]
    ))

def __castToInt(*args):
    """
    Cast the input args to int.
    """
    return list(map(int, args))


# sum
Template.registerProcedure(
    'sum',
    sumInt
)

# subtraction
Template.registerProcedure(
    'sub',
    subtractInt
)

# multiply
Template.registerProcedure(
    'mult',
    multiplyInt
)

# divide
Template.registerProcedure(
    'div',
    divideInt
)

# minimum
Template.registerProcedure(
    'min',
    minimumInt
)

# maximum
Template.registerProcedure(
    'max',
    maximumInt
)

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

def roundNumber(number):
    """
    Round a float point number.
    """
    return int(round(float(number)))

def even(number):
    """
    Procedure used transform the input number to an even number.
    """
    number = int(number)
    return number - 1 if number % 2 else number

def odd(number):
    """
    Procedure used transform the input number to an odd number.
    """
    number = int(number)
    return number if number % 2 else number - 1

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

# round
Template.registerProcedure(
    'round',
    roundNumber
)

# even
Template.registerProcedure(
    'even',
    even
)

# odd
Template.registerProcedure(
    'odd',
    odd
)

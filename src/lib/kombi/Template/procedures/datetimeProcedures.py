"""
Basic datetime functions.
"""

import datetime
from ..Template import Template

def yyyy():
    """
    Return the year formatted by 4 digits.
    """
    return datetime.datetime.now().strftime("%Y")

def yy():
    """
    Return the year formatted by 2 digits.
    """
    return datetime.datetime.now().strftime("%y")

def mm():
    """
    Return the month formatted by 2 digits.
    """
    return datetime.datetime.now().strftime("%m")

def dd():
    """
    Return the day formatted by 2 digits.
    """
    return datetime.datetime.now().strftime("%d")

def hour():
    """
    Return the hour formatted by 2 digits (24 hours format).
    """
    return datetime.datetime.now().strftime("%H")

def minute():
    """
    Return the minutes formatted by 2 digits.
    """
    return datetime.datetime.now().strftime("%d")

def second():
    """
    Return the seconds formatted by 2 digits.
    """
    return datetime.datetime.now().strftime("%S")


# registering template procedures
Template.registerProcedure(
    'yyyy',
    yyyy
)

Template.registerProcedure(
    'yy',
    yy
)

Template.registerProcedure(
    'mm',
    mm
)

Template.registerProcedure(
    'dd',
    dd
)

Template.registerProcedure(
    'hour',
    hour
)

Template.registerProcedure(
    'minute',
    minute
)

Template.registerProcedure(
    'second',
    second
)

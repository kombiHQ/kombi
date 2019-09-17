"""
Basic text functions.
"""

from ..Template import Template

def upper(string):
    """
    Return string converted to upper case.
    """
    return str(string).upper()

def concat(*args):
    """
    Return a concatenated string.
    """
    return ''.join(args)

def lower(string):
    """
    Return string converted to lower case.
    """
    return str(string).lower()

def replace(text, searchValue, replaceValue):
    """
    Return a string where all search value are replaced by the replace value.
    """
    return text.replace(searchValue, replaceValue)

def remove(text, removeValue):
    """
    Return a string where all remove value are removed from the text.
    """
    return text.replace(removeValue, '')


# upper case
Template.registerProcedure(
    'upper',
    upper
)

# concatenate
Template.registerProcedure(
    'concat',
    concat
)

# lower case
Template.registerProcedure(
    'lower',
    lower
)

# lower case
Template.registerProcedure(
    'lower',
    lower
)

# replace
Template.registerProcedure(
    'replace',
    replace
)

# remove
Template.registerProcedure(
    'remove',
    remove
)

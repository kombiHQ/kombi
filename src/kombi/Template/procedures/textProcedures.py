"""
Basic text functions.
"""

import re
from ..Template import Template
from fnmatch import fnmatch

def sliceText(value, pattern):
    """
    Slice characters of the input value.

    It works in the same way as the slice in python, for instance: (slice abc 1:-1)
    """
    parts = list(map(lambda x: None if x.strip() == '' else int(x), pattern.split('::' if '::' in pattern else ':')))
    if len(parts) > 1 and '::' in pattern:
        return value[parts[0]::parts[1]]
    elif len(parts) > 1 and ':' in pattern:
        return value[parts[0]:parts[1]]
    return value[parts[0]]

def repeat(string, interactions=1):
    """
    Return a string that repeats itself based on the number of interactions.
    """
    return string * int(interactions)

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

def capitalize(string):
    """
    Return string capitalized.
    """
    return str(string).capitalize()

def lower(string):
    """
    Return string converted to lower case.
    """
    return str(string).lower()

def fallback(fallbackValue, mainValue=""):
    """
    Return the fallback value when main value is empty.
    """
    return mainValue if mainValue else fallbackValue

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

def match(text, pattern):
    """
    Return if the text matches the pattern (fnmatch pattern).
    \todo: needs test
    """
    return int(fnmatch(text, pattern))

def length(text=''):
    """
    Return the length of the text.
    \todo: needs test
    """
    return len(text)

def undefined(text=''):
    """
    Return if the text is empty.
    \todo: needs test
    """
    return int(len(text) == 0)

def defined(text):
    """
    Return if the text is not empty.
    \todo: needs test
    """
    return int(len(text) > 0)

def equal(a, b):
    """
    Return if the texts are the same.
    \todo: needs test (Also, make sure any boolean value returned by any procedure is automatically converted to int then string)
    """
    return int(a == b)

def different(a, b):
    """
    Return if the texts are different.
    \todo: needs test
    """
    return int(a != b)

def splitPart(input, string, resultIndex=0):
    """
    Return the part of the split string.
    \todo: needs test
    """
    try:
        return input.split(string)[int(resultIndex)]
    except IndexError:
        return ''

def camelCaseToSpaced(text):
    """
    Return the input camelCase string to spaced.
    """
    return text[0].upper() + re.sub(r"([a-z])([A-Z\(\{\<])", r"\g<1> \g<2>", text[1:])


# slice
Template.registerProcedure(
    'slice',
    sliceText
)

# fallback
Template.registerProcedure(
    'fallback',
    fallback
)

# repeat
Template.registerProcedure(
    'repeat',
    repeat
)

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

# capitalize
Template.registerProcedure(
    'capitalize',
    capitalize
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

# match
Template.registerProcedure(
    'match',
    match
)

# length
Template.registerProcedure(
    'len',
    length
)

# undefined
Template.registerProcedure(
    'undefined',
    undefined
)

# defined
Template.registerProcedure(
    'defined',
    defined
)

# equal
Template.registerProcedure(
    'equal',
    equal
)

# different
Template.registerProcedure(
    'different',
    different
)

# split part
Template.registerProcedure(
    'splitpart',
    splitPart
)

Template.registerProcedure(
    'camelcasetospaced',
    camelCaseToSpaced
)
